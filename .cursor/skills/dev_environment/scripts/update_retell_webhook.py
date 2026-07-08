#!/usr/bin/env python3
import json
import os
import sys
import argparse


def build_webhook_url(args: argparse.Namespace) -> str:
    if args.url:
        return args.url.rstrip("/")
    tunnel_url = args.tunnel_url.rstrip("/")
    return f"{tunnel_url}{args.webhook_path}"


def print_json(payload: dict) -> None:
    print(json.dumps(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update Retell webhook URL for local development."
    )
    parser.add_argument(
        "--url",
        help="Full webhook URL destination (alternative to --tunnel-url).",
    )
    parser.add_argument(
        "--tunnel-url",
        help="Tunnel base URL (e.g. https://abc.trycloudflare.com).",
    )
    parser.add_argument(
        "--webhook-path",
        default=os.environ.get("RETELL_WEBHOOK_PATH", "/webhooks/retell"),
        help="Webhook path used with --tunnel-url (default: /webhooks/retell).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply update. Without this flag, runs in dry-run mode.",
    )
    parser.add_argument(
        "--agent-id",
        help="Target Retell Agent ID. Falls back to RETELL_AGENT_ID env var.",
    )
    args = parser.parse_args()

    if not args.url and not args.tunnel_url:
        print_json(
            {
                "status": "error",
                "message": "Provide --url or --tunnel-url.",
            }
        )
        return 2

    webhook_url = build_webhook_url(args)

    if not args.apply:
        print_json(
            {
                "status": "dry-run",
                "webhook_url": webhook_url,
                "message": "Pass --apply to perform the update.",
            }
        )
        return 0

    # Resolve agent ID (prioritize explicit CLI argument, fall back to environment)
    agent_id = args.agent_id or os.environ.get("RETELL_AGENT_ID")
    api_key = os.environ.get("RETELL_API_KEY")

    if not api_key:
        print_json(
            {
                "status": "error",
                "message": "RETELL_API_KEY environment variable is missing.",
            }
        )
        return 1

    if not agent_id:
        print_json(
            {
                "status": "error",
                "message": "No Agent ID provided. Pass --agent-id or set RETELL_AGENT_ID.",
            }
        )
        return 1

    try:
        from retell import Retell
    except Exception as e:
        print_json(
            {
                "status": "error",
                "message": f"Retell SDK import failed: {str(e)}",
            }
        )
        return 1

    try:
        client = Retell(api_key=api_key)
        client.agent.update(agent_id=agent_id, webhook_url=webhook_url)
        print_json(
            {
                "status": "success",
                "agent_id": agent_id,
                "webhook_url": webhook_url,
            }
        )
        return 0

    except Exception as e:
        print_json({"status": "error", "message": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())
