def health_status() -> dict[str, str]:
    return {
        "service": "ligent-sample-app",
        "status": "ok",
    }


if __name__ == "__main__":
    print(health_status())
