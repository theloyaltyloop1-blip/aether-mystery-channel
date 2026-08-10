"""
AETHER - batch publish
Runs auto_publish's full pipeline N times in a row. Stops early and reports
clearly if YouTube's daily upload quota is hit (free tier: 10,000 units/day,
1,600 units per upload -> ~6 uploads/day max), instead of failing silently.
"""
import sys

from googleapiclient.errors import HttpError

from auto_publish import main as publish_one


def run_batch(count: int) -> None:
    succeeded = 0
    for i in range(count):
        print(f"\n=== Run {i + 1}/{count} ===", flush=True)
        try:
            publish_one()
            succeeded += 1
        except HttpError as e:
            if e.status_code == 403 and "quota" in str(e).lower():
                print(
                    f"\nYouTube daily upload quota reached after {succeeded} successful "
                    f"uploads. Remaining topics will go out via the 4x/day scheduled runs "
                    f"once the quota resets.",
                    flush=True,
                )
                break
            print(f"Run {i + 1} failed with API error: {e}", flush=True)
        except SystemExit as e:
            print(f"Run {i + 1} failed: {e}", flush=True)
        except Exception as e:
            print(f"Run {i + 1} failed: {e}", flush=True)

    print(f"\nBatch complete: {succeeded}/{count} videos published.", flush=True)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_batch(n)
