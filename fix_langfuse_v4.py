"""
Fix outdated Langfuse v4 code patterns in HTML tutorial files.
"""
import os
import re

TUTORIAL_DIR = "/Users/praveensubbarao2026/work/langfuse-python-tutorial/Tutorial Documentation"

FILES_ALL = [
    "langfuse_day1_hour1_ollama.html",
    "langfuse_day1_hour2_ollama.html",
    "langfuse_day1_hour3_ollama.html",
    "langfuse_day2_hour1_ollama.html",
    "langfuse_day2_hour2_ollama.html",
    "langfuse_day2_hour3_ollama.html",
    "langfuse_day3_all_hours_ollama.html",
]

FILE_DAY3 = "langfuse_day3_all_hours_ollama.html"


def count_and_replace(content, old, new, label=""):
    count = content.count(old)
    if count:
        print(f"    [{label or 'replace'}] {count}x: {old[:60]!r}...")
    return content.replace(old, new), count


def fix_usage_patterns(content):
    """Fix all usage= patterns across all files."""
    total = 0
    new_content = content

    # ── Pattern A: single-line with response.usage ───────────────────────────
    old_a = 'usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens})'
    new_a = 'usage_details={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens})'
    new_content, n = count_and_replace(new_content, old_a, new_a, "A1-single-response")
    total += n

    old_a2 = 'usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens},'
    new_a2 = 'usage_details={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens},'
    new_content, n = count_and_replace(new_content, old_a2, new_a2, "A2-single-response-comma")
    total += n

    # ── Pattern B: single-line with resp.usage ───────────────────────────────
    old_b = 'usage={"input": resp.usage.prompt_tokens, "output": resp.usage.completion_tokens})'
    new_b = 'usage_details={"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens})'
    new_content, n = count_and_replace(new_content, old_b, new_b, "B-single-resp")
    total += n

    # ── Pattern C: multiline with 2 fields (input + output) — day1h2, day1h3, day2h1 ──
    # Multiline with 2 spans:
    #   usage={
    #       <span class="st">"input"</span>:  response.usage.prompt_tokens,
    #       <span class="st">"output"</span>: response.usage.completion_tokens,
    #   },
    # Handle varying whitespace / indentation variants

    # day1_hour2 line 984: 4-space indent inside @observe
    old_c1 = (
        '        usage={\n'
        '            <span class="st">"input"</span>:  response.usage.prompt_tokens,\n'
        '            <span class="st">"output"</span>: response.usage.completion_tokens,\n'
        '        },'
    )
    new_c1 = (
        '        usage_details={\n'
        '            <span class="st">"input_tokens"</span>:  response.usage.prompt_tokens,\n'
        '            <span class="st">"output_tokens"</span>: response.usage.completion_tokens,\n'
        '        },'
    )
    new_content, n = count_and_replace(new_content, old_c1, new_c1, "C1-multiline-2field-8sp")
    total += n

    # day1_hour3 line 333 / day2_hour1 line 725: same indent but no extra space after "input":
    old_c2 = (
        '            usage={\n'
        '                <span class="st">"input"</span>:  response.usage.prompt_tokens,\n'
        '                <span class="st">"output"</span>: response.usage.completion_tokens,\n'
        '            },'
    )
    new_c2 = (
        '            usage_details={\n'
        '                <span class="st">"input_tokens"</span>:  response.usage.prompt_tokens,\n'
        '                <span class="st">"output_tokens"</span>: response.usage.completion_tokens,\n'
        '            },'
    )
    new_content, n = count_and_replace(new_content, old_c2, new_c2, "C2-multiline-2field-12sp")
    total += n

    # ── Pattern D: multiline with 3 fields (input + output + total) ──────────
    # day1_hour2 line 734 and day3 line 737

    # day1_hour2: 16-space indent
    old_d1 = (
        '                usage={\n'
        '                    <span class="st">"input"</span>:  response.usage.prompt_tokens,\n'
        '                    <span class="st">"output"</span>: response.usage.completion_tokens,\n'
        '                    <span class="st">"total"</span>:  response.usage.total_tokens,\n'
        '                },'
    )
    new_d1 = (
        '                usage_details={\n'
        '                    <span class="st">"input_tokens"</span>:  response.usage.prompt_tokens,\n'
        '                    <span class="st">"output_tokens"</span>: response.usage.completion_tokens,\n'
        '                    <span class="st">"total_tokens"</span>:  response.usage.total_tokens,\n'
        '                },'
    )
    new_content, n = count_and_replace(new_content, old_d1, new_d1, "D1-multiline-3field-16sp")
    total += n

    # day3: 8-space indent with extra spaces for alignment
    old_d2 = (
        '        usage={\n'
        '            <span class="st">"input"</span>:          response.usage.prompt_tokens,\n'
        '            <span class="st">"output"</span>:         response.usage.completion_tokens,\n'
        '            <span class="st">"total"</span>:          response.usage.total_tokens,\n'
    )
    new_d2 = (
        '        usage_details={\n'
        '            <span class="st">"input_tokens"</span>:          response.usage.prompt_tokens,\n'
        '            <span class="st">"output_tokens"</span>:         response.usage.completion_tokens,\n'
        '            <span class="st">"total_tokens"</span>:          response.usage.total_tokens,\n'
    )
    new_content, n = count_and_replace(new_content, old_d2, new_d2, "D2-multiline-3field-day3")
    total += n

    return new_content, total


def fix_day3_fetch_patterns(content):
    """Fix fetch_traces / fetch_scores patterns in day3 file."""
    total = 0
    new_content = content

    # fetch_traces(tags=["qa"], limit=20).data  (multiline)
    old_1 = (
        'langfuse.<span class="fn">fetch_traces</span>(\n'
        '    tags=[<span class="st">"qa"</span>],\n'
        '    limit=<span class="nu">20</span>,\n'
        ').data'
    )
    new_1 = (
        'langfuse.api.trace.<span class="fn">list</span>(\n'
        '    tags=[<span class="st">"qa"</span>],\n'
        '    limit=<span class="nu">20</span>,\n'
        ').data'
    )
    new_content, n = count_and_replace(new_content, old_1, new_1, "fetch_traces-qa-20")
    total += n

    # fetch_scores(trace_id=...) single-line
    old_2 = 'langfuse.<span class="fn">fetch_scores</span>(trace_id=trace.id, name=<span class="st">"user_feedback"</span>).data'
    new_2 = 'langfuse.api.scores.<span class="fn">get_many</span>(trace_id=trace.id, name=<span class="st">"user_feedback"</span>).data'
    new_content, n = count_and_replace(new_content, old_2, new_2, "fetch_scores-trace_id")
    total += n

    # recent = langfuse.fetch_traces(limit=10).data
    old_3 = 'recent = langfuse.<span class="fn">fetch_traces</span>(limit=<span class="nu">10</span>).data'
    new_3 = 'recent = langfuse.api.trace.<span class="fn">list</span>(limit=<span class="nu">10</span>).data'
    new_content, n = count_and_replace(new_content, old_3, new_3, "fetch_traces-limit10")
    total += n

    # scores = langfuse.fetch_scores(  (multiline)
    old_4 = 'scores = langfuse.<span class="fn">fetch_scores</span>(\n'
    new_4 = 'scores = langfuse.api.scores.<span class="fn">get_many</span>(\n'
    new_content, n = count_and_replace(new_content, old_4, new_4, "fetch_scores-multiline")
    total += n

    # low_quality = langfuse.fetch_traces(  (multiline)
    old_5 = 'low_quality = langfuse.<span class="fn">fetch_traces</span>(\n'
    new_5 = 'low_quality = langfuse.api.trace.<span class="fn">list</span>(\n'
    new_content, n = count_and_replace(new_content, old_5, new_5, "fetch_traces-low_quality")
    total += n

    return new_content, total


def fix_day3_callback_patterns(content):
    """Fix langfuse.callback -> langfuse.langchain and CallbackHandler args."""
    total = 0
    new_content = content

    # Import line: from langfuse.callback import CallbackHandler
    old_import = '<span class="kw">from</span> langfuse.callback <span class="kw">import</span> CallbackHandler'
    new_import = '<span class="kw">from</span> langfuse.langchain <span class="kw">import</span> CallbackHandler'
    new_content, n = count_and_replace(new_content, old_import, new_import, "callback-import")
    total += n

    # CallbackHandler instantiation — remove user_id/session_id/tags, add comment
    old_handler = (
        'langfuse_handler = <span class="fn">CallbackHandler</span>(\n'
        '    user_id=<span class="st">"user-123"</span>,\n'
        '    session_id=<span class="st">"langchain-demo"</span>,\n'
        '    tags=[<span class="st">"langchain"</span>, <span class="st">"day3"</span>],\n'
        ')'
    )
    new_handler = (
        'langfuse_handler = <span class="fn">CallbackHandler</span>()\n'
        '<span class="cm"># NOTE (v4): CallbackHandler no longer accepts user_id / session_id / tags.</span>\n'
        '<span class="cm"># Pass those via langfuse_context.update_current_trace() or</span>\n'
        '<span class="cm"># langfuse_context.propagate_attributes() inside your @observe-decorated functions.</span>'
    )
    new_content, n = count_and_replace(new_content, old_handler, new_handler, "CallbackHandler-args")
    total += n

    return new_content, total


def process_file(filepath, is_day3=False):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    file_total = 0

    print(f"\n  Processing: {os.path.basename(filepath)}")

    content, n = fix_usage_patterns(content)
    file_total += n

    if is_day3:
        content, n = fix_day3_fetch_patterns(content)
        file_total += n
        content, n = fix_day3_callback_patterns(content)
        file_total += n

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  => CHANGED ({file_total} replacement(s))")
    else:
        print(f"  => No changes")

    return file_total


def main():
    grand_total = 0
    results = {}

    for fname in FILES_ALL:
        fpath = os.path.join(TUTORIAL_DIR, fname)
        is_day3 = (fname == FILE_DAY3)
        n = process_file(fpath, is_day3=is_day3)
        results[fname] = n
        grand_total += n

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for fname, n in results.items():
        status = f"{n} replacement(s)" if n else "no changes"
        print(f"  {fname}: {status}")
    print(f"\n  Grand total replacements: {grand_total}")


if __name__ == "__main__":
    main()
