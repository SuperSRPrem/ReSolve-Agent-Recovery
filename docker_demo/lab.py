import json
import subprocess
import sys
import urllib.error
import urllib.request


CONTAINER_NAME = "resolve-demo-service"
HEALTH_URL = "http://127.0.0.1:18080/health"


def runDocker(arguments):
    try:
        result = subprocess.run(
            ["docker", *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=15
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Docker CLI was not found.",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Docker command timed out.",
        }


def containerRunning():
    result = runDocker([
        "inspect",
        "-f",
        "{{.State.Running}}",
        CONTAINER_NAME
    ])

    if not result["success"]:
        return False

    return (
        result["stdout"]
        .strip()
        .lower()
        == "true"
    )


def checkHealth():
    try:
        request = urllib.request.Request(
            HEALTH_URL,
            method="GET"
        )

        with urllib.request.urlopen(
            request,
            timeout=2
        ) as response:

            body = response.read().decode("utf-8")

            return {
                "healthy": (
                    200 <= response.status < 300
                ),
                "statusCode": response.status,
                "body": json.loads(body),
            }

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError
    ) as error:

        return {
            "healthy": False,
            "statusCode": None,
            "error": str(error),
        }


def showStatus():
    print()
    print("=" * 60)
    print("RESOLVE DOCKER LAB STATUS")
    print("=" * 60)

    print(
        "Container running:",
        containerRunning()
    )

    print(
        "Health:",
        json.dumps(
            checkHealth(),
            indent=2
        )
    )


def breakService():
    print(
        f"Stopping {CONTAINER_NAME}..."
    )

    result = runDocker([
        "stop",
        CONTAINER_NAME
    ])

    if result["success"]:
        print("Service stopped.")
    else:
        print(
            "Failed:",
            result["stderr"]
        )

    showStatus()


def recoverService():
    print(
        f"Starting {CONTAINER_NAME}..."
    )

    result = runDocker([
        "start",
        CONTAINER_NAME
    ])

    if result["success"]:
        print("Service started.")
    else:
        print(
            "Failed:",
            result["stderr"]
        )

    showStatus()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:"
        )
        print(
            "python docker_demo/lab.py status"
        )
        print(
            "python docker_demo/lab.py break"
        )
        print(
            "python docker_demo/lab.py recover"
        )
        return

    command = sys.argv[1].lower()

    if command == "status":
        showStatus()

    elif command == "break":
        breakService()

    elif command == "recover":
        recoverService()

    else:
        print(
            f"Unknown command: {command}"
        )


if __name__ == "__main__":
    main()
