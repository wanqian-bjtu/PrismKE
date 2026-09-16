from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prismke_autodl.sh"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="AutoDL scripts require POSIX")


def _executable(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")
    path.chmod(0o755)


@dataclass
class FakeRuntime:
    project: Path
    state: Path
    env: dict[str, str]

    def run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), *arguments],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )


@pytest.fixture
def fake_runtime(tmp_path: Path) -> FakeRuntime:
    project = tmp_path / "PrismKE"
    state = tmp_path / "state"
    fake_bin = tmp_path / "bin"
    for directory in (
        project / ".venv" / "bin",
        project / "runtime" / "neo4j" / "current" / "bin",
        project / "runtime" / "neo4j" / "logs",
        project / "runtime" / "logs",
        project / "scripts",
        state,
        fake_bin,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    (project / ".env").write_text(
        "PRISMKE_LLM_API_KEY=sk-private-do-not-print\n", encoding="utf-8"
    )
    (project / "runtime" / "neo4j" / "logs" / "neo4j.log").write_text(
        "neo4j ready\n", encoding="utf-8"
    )

    _executable(
        project / ".venv" / "bin" / "python",
        """
#!/usr/bin/env bash
if [[ "$1" == "-c" ]]; then
  echo "${FAKE_API_PORT:-18000}"
  exit 0
fi
if [[ "$1" == "-" ]]; then
  test -f "${FAKE_STATE}/port-$2"
  exit $?
fi
exit 2
""",
    )
    _executable(fake_bin / "uv", "#!/usr/bin/env bash\nexit 0")
    _executable(
        project / "runtime" / "neo4j" / "current" / "bin" / "neo4j",
        """
#!/usr/bin/env bash
case "$1" in
  status)
    if [[ -f "${FAKE_STATE}/neo4j" ]]; then
      echo "Neo4j is running at pid 1111"
      exit 0
    fi
    exit 3
    ;;
  stop)
    rm -f "${FAKE_STATE}/neo4j" "${FAKE_STATE}/port-7474" "${FAKE_STATE}/port-7687"
    echo "Neo4j stopped"
    ;;
  *) exit 2 ;;
esac
""",
    )
    _executable(
        project / "scripts" / "start_neo4j_autodl.sh",
        """
#!/usr/bin/env bash
if [[ "${FAKE_NEO4J_FAIL:-0}" == "1" ]]; then
  exit 1
fi
touch "${FAKE_STATE}/neo4j" "${FAKE_STATE}/port-7474" "${FAKE_STATE}/port-7687"
echo "Neo4j started"
""",
    )
    _executable(
        fake_bin / "tmux",
        """
#!/usr/bin/env bash
command="$1"
shift
session=""
previous=""
for argument in "$@"; do
  if [[ "${previous}" == "-t" || "${previous}" == "-s" ]]; then
    session="${argument}"
    break
  fi
  previous="${argument}"
done
case "${command}" in
  has-session) test -f "${FAKE_STATE}/session-${session}" ;;
  new-session)
    [[ "${FAKE_TMUX_FAIL:-0}" != "1" ]] || exit 1
    touch "${FAKE_STATE}/session-${session}" "${FAKE_STATE}/port-${FAKE_API_PORT:-18000}"
    echo "new-session:${session}" >>"${FAKE_STATE}/events"
    ;;
  send-keys|kill-session)
    rm -f "${FAKE_STATE}/session-${session}" "${FAKE_STATE}/port-${FAKE_API_PORT:-18000}"
    echo "stop-session:${session}" >>"${FAKE_STATE}/events"
    ;;
  list-panes) echo 2222 ;;
  *) exit 2 ;;
esac
""",
    )
    _executable(
        fake_bin / "curl",
        """
#!/usr/bin/env bash
if [[ "${FAKE_HEALTH:-ok}" == "degraded" ]]; then
  echo '{"status":"degraded","graph":{"healthy":false}}'
  exit 0
fi
if [[ -f "${FAKE_STATE}/neo4j" ]] && compgen -G "${FAKE_STATE}/session-*" >/dev/null; then
  echo '{"status":"ok","graph":{"backend":"neo4j","healthy":true}}'
  exit 0
fi
exit 7
""",
    )
    _executable(
        fake_bin / "tail",
        """
#!/usr/bin/env bash
for argument in "$@"; do
  if [[ "${argument}" == "-F" ]]; then
    echo "tail-follow" >>"${FAKE_STATE}/events"
    exit 0
  fi
done
exec /usr/bin/tail "$@"
""",
    )

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "FAKE_STATE": str(state),
            "FAKE_API_PORT": "18000",
            "PRISMKE_PROJECT_DIR": str(project),
            "PRISMKE_UV_BIN": str(fake_bin / "uv"),
            "PRISMKE_START_TIMEOUT": "1",
        }
    )
    return FakeRuntime(project=project, state=state, env=env)


def test_help_and_unknown_command(fake_runtime: FakeRuntime) -> None:
    help_result = fake_runtime.run("--help")
    unknown_result = fake_runtime.run("unknown")
    assert help_result.returncode == 0
    assert "prismke_autodl.sh start" in help_result.stdout
    assert unknown_result.returncode == 2
    assert "Usage:" in unknown_result.stderr


def test_full_lifecycle_is_idempotent_and_redacts_environment(
    fake_runtime: FakeRuntime,
) -> None:
    first = fake_runtime.run("start")
    second = fake_runtime.run("start")
    status = fake_runtime.run("status")
    health = fake_runtime.run("health")

    assert first.returncode == second.returncode == status.returncode == health.returncode == 0
    assert "already healthy" in second.stdout
    assert "sk-private-do-not-print" not in first.stdout + first.stderr + status.stdout
    events = (fake_runtime.state / "events").read_text(encoding="utf-8")
    assert events.count("new-session:prismke-web") == 1

    web_log = fake_runtime.project / "runtime" / "logs" / "prismke-web.log"
    web_log.write_text("line one\nline two\n", encoding="utf-8")
    logs = fake_runtime.run("logs", "web", "--lines", "1")
    follow = fake_runtime.run("logs", "web", "--lines", "1", "--follow")
    assert logs.returncode == follow.returncode == 0
    assert logs.stdout == "line two\n"
    assert "tail-follow" in (fake_runtime.state / "events").read_text(encoding="utf-8")

    stopped = fake_runtime.run("stop")
    stopped_again = fake_runtime.run("stop")
    final_status = fake_runtime.run("status")
    assert stopped.returncode == stopped_again.returncode == 0
    assert "already stopped" in stopped_again.stdout
    assert final_status.returncode == 1


def test_port_conflict_is_detected_before_starting_neo4j(
    fake_runtime: FakeRuntime,
) -> None:
    (fake_runtime.state / "port-18000").touch()
    result = fake_runtime.run("start")
    assert result.returncode == 1
    assert "Port 18000 is already in use" in result.stderr
    assert not (fake_runtime.state / "neo4j").exists()


@pytest.mark.parametrize("failure", ["health", "tmux"])
def test_failed_web_start_rolls_back_new_neo4j(
    fake_runtime: FakeRuntime, failure: str
) -> None:
    if failure == "health":
        fake_runtime.env["FAKE_HEALTH"] = "degraded"
    else:
        fake_runtime.env["FAKE_TMUX_FAIL"] = "1"
    result = fake_runtime.run("start")
    assert result.returncode == 1
    assert not (fake_runtime.state / "neo4j").exists()
    assert not (fake_runtime.state / "session-prismke-web").exists()


def test_web_log_rotates_and_logs_validate_arguments(fake_runtime: FakeRuntime) -> None:
    web_log = fake_runtime.project / "runtime" / "logs" / "prismke-web.log"
    with web_log.open("wb") as stream:
        stream.seek(10 * 1024 * 1024)
        stream.write(b"x")
    result = fake_runtime.run("start")
    invalid = fake_runtime.run("logs", "web", "--lines", "0")
    assert result.returncode == 0
    assert web_log.with_suffix(".log.1").exists()
    assert invalid.returncode == 1
    assert "positive integer" in invalid.stderr
