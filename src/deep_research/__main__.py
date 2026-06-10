"""CLI entry point.  Run:  python -m deep_research "your topic"   (or: deep-research "...")"""
import argparse

from .pipeline import run


def main():
    ap = argparse.ArgumentParser(
        prog="deep-research",
        description="Write an in-depth, fully-cited, hallucination-free research report on any subject.",
    )
    ap.add_argument("topic", nargs="+", help='the subject to research, e.g. "Sydney Sweeney"')
    ap.add_argument("--no-pdf", action="store_true", help="skip PDF rendering (Markdown only)")
    args = ap.parse_args()

    summary = run(" ".join(args.topic), make_pdf=not args.no_pdf)
    print(f"\nDone — {summary['words']:,} words, {summary['sentences']} grounded sentences, "
          f"{summary['sources']} sources.")


if __name__ == "__main__":
    main()
