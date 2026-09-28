"""Bounded independent Skill consumer trial. No fixture plans are read."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GEOMETRY = ROOT / "outputs/calibration/illustration/vector-study/semantic-study-v4.svg"
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solid(identifier, role, color, **extra):
    return {"id": identifier, "role": role, "paint": {"type": "solid", "color": color}, **extra}


def field(identifier, colors):
    return {"id": identifier, "role": "surface", "paint": {"type": "linear", "from": [100, 100], "to": [1100, 1150], "colors": colors}}


def shadow(identifier, owner, color, reason):
    return solid(identifier, "occlusion-shadow", color, owner=owner, anchor="receiver-boundary", reason=reason)


def prepare():
    """Independent choices made from the actual references and source geometry."""
    for profile in ("short", "full"):
        prompt = OUT / profile / "prompt.zh-CN.md"
        if not prompt.is_file():
            raise RuntimeError("The real prompt must predate the plan")
        full = profile == "full"
        layers = [solid("coverage-underpaint", "underpaint", "#514d59" if full else "#55515e")]
        layers.append(field("face-visible-region", ["#fff3e8", "#f8e5db"]) if full else solid("face-visible-region", "surface", "#fff1e4"))
        layers.append(field("hair-base", ["#595561", "#4f4b57"]) if full else solid("hair-base", "surface", "#595560"))
        hair_shadow = "#45424c" if full else "#4d4954"
        layers.extend([
            shadow("left-fringe-shadow", "hair-base", hair_shadow, "左侧大刘海覆盖侧后发，暗面沿左侧发束边界向脸颊收拢。"),
            shadow("center-fold-shadow", "hair-base", hair_shadow, "中央刘海向右覆盖相邻发面，暗面跟随下垂转折，不作为镜面高光。"),
            shadow("right-crown-shadow", "hair-base", hair_shadow, "右侧外发束包覆内侧发层，沿右侧主弧保留单档暗面。"),
        ])
        layers.append(field("coral-base", ["#f58b9a", "#e7778a"]) if full else solid("coral-base", "surface", "#f397a2"))
        coral_shadow = "#d96c80" if full else "#df838e"
        layers.extend([
            shadow("coral-left-return", "coral-base", coral_shadow, "左上珊瑚侧束的大回卷盖住根部内面，暗面落在卷内并触及回卷边。"),
            shadow("coral-left-fold", "coral-base", coral_shadow, "左侧下层回卷被上层覆盖，使用同一材料的一档暗色。"),
            shadow("coral-right-fold", "coral-base", coral_shadow, "右侧珊瑚回卷包围的折返内侧位于前层之后，保留有边界的内暗面。"),
        ])
        layers.append(field("halo-base", ["#70d2c5", "#5bc2ba"]) if full else solid("halo-base", "surface", "#76d4c7"))
        layers.append(shadow("halo-inner-shadow", "halo-base", "#4caeaa" if full else "#60bdba", "青环的内缘背向主受光侧，暗面与内轮廓相接；不添加独立亮面。"))
        layers.extend([
            solid("cheek-left", "blush", "#f9cbc8" if full else "#fad2cf", owner="face-visible-region"),
            solid("cheek-right", "blush", "#f9cbc8" if full else "#fad2cf", owner="face-visible-region"),
            solid("eye-left", "eye", "#26252f"),
            solid("eye-right", "eye", "#26252f"),
        ])
        plan = {
            "schema": "aikon.paint-plan.v1", "geometry_sha256": sha(GEOMETRY), "profile": profile,
            "notes": "Independent Skill consumer paint trial. Geometry locked; source numeric eye/pose compliance is not newly claimed. No fixture plan was read.",
            "reference_bindings": {"illustration": "ref/feedback/2026-09-29/accepted-composition-defective-paint.png", "deepseek": "ref/user-mode/r1.png"},
            "layers": layers,
        }
        base = OUT / profile / "r001"
        save(base / "paint.json", plan)
        save(base / "input-record.json", {"profile": profile, "prompt_sha256": sha(prompt), "prompt_mtime_ns": prompt.stat().st_mtime_ns, "plan_written_at_ns": time.time_ns(), "geometry_sha256": sha(GEOMETRY), "references": {name: sha(ROOT / name) for name in ["ref/feedback/2026-09-29/accepted-composition-defective-paint.png", "ref/feedback/2026-09-29/annotated-paint-defects.png", "ref/user-mode/r1.png"]}})
    print("independent plans prepared after prompts")


def run(profile, revision):
    from PIL import Image, ImageDraw
    from tools import paint_checks, render_svg, analyze_paint_fields
    base = OUT / profile / revision
    plan = json.loads((base / "paint.json").read_text(encoding="utf-8"))
    commands = []
    started = time.time()
    def command(arguments, label):
        full_command = [sys.executable, "-B", *arguments]
        result = subprocess.run(full_command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=45, check=False)
        commands.append({"argv": full_command, "cwd": str(ROOT), "timeout_seconds": 45, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        save(base / (label + ".command.json"), commands[-1])
        if result.returncode:
            raise RuntimeError(label + " failed: " + result.stderr)
    command(["skills/aikon/scripts/paint_svg.py", "--geometry", str(GEOMETRY), "--plan", str(base / "paint.json"), "--output", str(base / "icon.svg"), "--report", str(base / "compile.json")], "compile")
    print(profile, revision, "compiled", flush=True)
    for size in (1024, 128, 48, 24):
        command(["tools/render_svg.py", str(base / "icon.svg"), "--output", str(base / f"preview-{size}.png"), "--size", str(size)], f"render-{size}")
    svg = (base / "icon.svg").read_text(encoding="utf-8")
    paint_checks.check_geometry_lock(GEOMETRY.read_bytes(), svg, plan)
    actual = paint_checks.check_compiled_structure(svg, plan)
    masks = paint_checks.raster_masks(svg, plan, size=1024, output=base / "owner-masks")
    ownership = paint_checks.ownership_checks(masks, plan, size=1024)
    save(base / "ownership.json", ownership)
    contract, visible, exclusions = paint_checks.visible_material_contract(svg, masks, plan, dict(analyze_paint_fields.DEFAULT_RULES))
    # This trial uses frozen API defaults rather than claiming it calibrated r1.
    contract["threshold_provenance"] = "analyze_paint_fields.DEFAULT_RULES consumed unchanged by independent trial; no threshold tuning against this candidate"
    save(base / "visible-mask-exclusions.json", exclusions)
    save(base / "pixel-contract.json", contract)
    with Image.open(base / "preview-1024.png") as im:
        report, maps = analyze_paint_fields.analyze_image(im, contract, visible)
        analyze_paint_fields.save_evidence(base / "paint-evidence", report, maps, contract)
        rgba = im.convert("RGBA")
        dark = Image.new("RGBA", rgba.size, "#191a1f")
        dark.alpha_composite(rgba)
        light = Image.new("RGBA", rgba.size, "#faf7f2")
        light.alpha_composite(rgba)
        dark.convert("RGB").save(base / "preview-dark.png")
        light.convert("RGB").save(base / "preview-light.png")
        dark.crop((260, 200, 790, 720)).save(base / "hair-detail.png")
    # Layout sheet uses already rendered sizes without rescaling the pixels.
    sheet = Image.new("RGB", (680, 280), "#faf7f2")
    draw = ImageDraw.Draw(sheet)
    for column, size in enumerate((128, 48, 24)):
        with Image.open(base / f"preview-{size}.png") as im:
            for row, color in enumerate(("#faf7f2", "#191a1f")):
                x, y = column * 220 + 20, row * 140 + 5
                sheet.paste(color, (x, y, x + 150, y + 130))
                sheet.paste(im, (x, y), im)
                draw.text((x + 155, y + 10), str(size), fill="#333333")
    sheet.save(base / "small-sizes.png")
    summary = {"profile": profile, "revision": revision, "pid": os.getpid(), "parent_pid": os.getppid(), "start_time_unix": started, "elapsed_seconds": time.time() - started, "renderer": render_svg.backend_info(), "geometry_lock": "passed", "compiled_structure": {"status": "passed", "layers": actual}, "ownership_status": ownership["status"], "ownership_issues": ownership["issues"], "pixel_status": report["status"], "pixel_issues": report["issues"], "visual_review": "pending_actual_view", "user_acceptance": "not_claimed", "commands": commands, "tools_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [ROOT / "skills/aikon/scripts/paint_svg.py", ROOT / "tools/paint_checks.py", ROOT / "tools/analyze_paint_fields.py", ROOT / "tools/render_svg.py"]}}
    save(base / "run.json", summary)
    print(json.dumps({k: summary[k] for k in ("profile", "revision", "elapsed_seconds", "ownership_status", "ownership_issues", "pixel_status", "pixel_issues")}, ensure_ascii=False), flush=True)


def revise():
    """One bounded revision: remove only unsupported existing shadow overlays."""
    for profile in ("short", "full"):
        old = OUT / profile / "r001"
        plan = json.loads((old / "paint.json").read_text(encoding="utf-8"))
        ownership = json.loads((old / "ownership.json").read_text(encoding="utf-8"))
        rejected = {issue["layer"] for issue in ownership["issues"]}
        # Do not silently alter the plan if another failure class is found.
        if any(layer["role"] != "occlusion-shadow" for layer in plan["layers"] if layer["id"] in rejected):
            raise RuntimeError("Non-shadow ownership failure requires diagnosis")
        if not rejected:
            continue
        new = OUT / profile / "r002"
        new.mkdir(parents=True, exist_ok=True)
        with (new / "revision-prompt.zh-CN.md").open("x", encoding="utf-8") as stream:
            stream.write("# 一次有界修正指令\n\n保留 r001 已选主面、调色板与所有几何，不放宽任何阈值。实际 owner 检查否定以下已有阴影片的边界归属：" + "、".join(sorted(rejected)) + "。只移除这些片，另存 r002 并完整复跑实际渲染与 masks/像素检查。这一处理可能削弱内部发束分组，必须实际查看并报告，不能仅凭通过宣布美术合格。\n")
        revised = copy.deepcopy(plan)
        revised["layers"] = [layer for layer in revised["layers"] if layer["id"] not in rejected]
        revised["notes"] += " Revision r002 removes mechanically unanchored shadow overlays; no geometry or threshold changes."
        save(new / "paint.json", revised)
        save(new / "revision.json", {"parent": "r001", "removed_shadow_layers": sorted(rejected), "prompt_saved_before_plan": True, "changed_geometry": False, "changed_thresholds": False})
    print("one bounded revision prepared")


def finalize():
    from PIL import Image, ImageDraw
    from tools import paint_checks
    outputs = {profile: (OUT / profile / "r002/icon.svg").read_bytes() for profile in ("short", "full")}
    pair = paint_checks.check_profile_pair(outputs)
    binding = {"bindings": {"deepseek": {"reference": "ref/user-mode/r1.png", "roles": ["subject", "style"], "sha256": sha(ROOT / "ref/user-mode/r1.png")}}}
    save(OUT / "reference-binding.json", binding)
    binding_check = paint_checks.check_reference_binding(ROOT, OUT / "reference-binding.json")
    records = []
    for profile in ("short", "full"):
        for revision in ("r001", "r002"):
            base = OUT / profile / revision
            run_record = json.loads((base / "run.json").read_text(encoding="utf-8"))
            metrics = json.loads((base / "paint-evidence/metrics.json").read_text(encoding="utf-8"))
            compile_record = json.loads((base / "compile.json").read_text(encoding="utf-8"))
            surface_metrics = [{"id": region["id"], "grain_rms": region["texture"].get("grain_rms_0_255"), "mottle_rms": region["texture"].get("mottle_rms_0_255"), "sample_pixels": region["texture"].get("sample_pixels"), "sample_fraction": region["texture"].get("sample_fraction_of_region_interior"), "status": region["status"]} for region in metrics["regions"] if region["expectation"] == "smooth_field"]
            records.append({"profile": profile, "revision": revision, "geometry_lock": run_record["geometry_lock"], "structure": run_record["compiled_structure"]["status"], "ownership": run_record["ownership_status"], "pixels": run_record["pixel_status"], "ownership_issues": run_record["ownership_issues"], "pixel_issues": run_record["pixel_issues"], "gradient_count": compile_record["gradient_count"], "selected_layers": len(compile_record["retained_layers"]), "geometry_source_sha256": compile_record["geometry_source_sha256"], "layout_geometry_signature": compile_record["layout_geometry_signature"], "svg_sha256": compile_record["svg_sha256"], "surface_metrics": surface_metrics, "global_alpha_evidence": metrics["global_alpha_evidence"], "run_record": str((base / "run.json").relative_to(OUT)), "elapsed_seconds": run_record["elapsed_seconds"]})
    if len({record["layout_geometry_signature"] for record in records}) != 1:
        raise RuntimeError("Unexpected layout change between revisions or profiles")
    # All pixels here come from the final SVG renders, with review backgrounds only.
    for profile in ("short", "full"):
        base = OUT / profile / "r002"
        with Image.open(base / "preview-1024.png") as image:
            checker = Image.new("RGBA", image.size, "#eeeeee")
            draw = ImageDraw.Draw(checker)
            for y in range(0, 1024, 32):
                for x in range(0, 1024, 32):
                    if (x // 32 + y // 32) % 2:
                        draw.rectangle((x, y, x + 31, y + 31), fill="#c9c9c9")
            checker.alpha_composite(image)
            checker.convert("RGB").save(base / "preview-checker.png")
    result = {
        "schema": "aikon.independent-paint-consumer.v1", "date": "2026-09-29", "round": "illustration-paint-consumer-001",
        "scope": "Skill-guided independent paint plans on supplied geometry, same host/model family",
        "read_fixture_paint_plan": False, "imagegen_calls": 0, "network_image_uploads": 0,
        "prompt_precedes_plan": True, "revision_count_per_profile": 2, "bounded_corrections": 1,
        "source": str(GEOMETRY.relative_to(ROOT)), "source_sha256": sha(GEOMETRY),
        "profile_pair_check": {"status": "passed", "svg_sha256": pair}, "deepseek_binding_check": binding_check,
        "runs": records,
        "actual_visual_views": [f"{profile}/r002/{name}" for profile in ("short", "full") for name in ("preview-dark.png", "preview-light.png", "small-sizes.png")] + ["full/r002/hair-detail.png", "short/r001/preview-dark.png", "full/r001/preview-light.png", "full/r001/hair-detail.png"],
        "visual_review": {"status": "completed_refinement_needed", "positive": ["无用户圈注的星状高光、颗粒或斑驳观感", "两眼、近景裁切与主要身份配色仍可辨识", "主面连续，深浅展示底上未见明显残留黑底"], "remaining": ["移除中央无边界依据暗面后，中央大刘海过于整块，内部发束关系弱于用户完整图", "青环少量既有短阴影仍显拼片，owner像素通过没有证明转面自然", "珊瑚侧束的窄亮色残带来自大面相交/留白，仍需按曲线关系验收", "已有v4几何在顶部外发缘有局部折点，轮廓与饰件结构本轮未重建", "24px下主要色彩和双眼仍可辨，细部发流及环尖不能清楚辨别"]},
        "user_acceptance": "not_claimed", "full_icon_accepted": False,
        "limitations": ["没有证明任意新主体geometry理解", "没有执行其他harness或模型", "没有测量韩文/中文语言因果", "固定geometry沿用眼尺寸不一致、约2.3比例和约22.7度各自旋转，不宣称源profile几何合规", "像素默认阈值只检测限定缺陷，不代表自然光照或美术评分", "r1 binding检查未生成DeepSeek新图"],
        "tooling_incident": {"run": "short/r001", "issue": "compiler stdout decoding failed in Windows reader thread; compile.command.json stdout is null", "artifact_status": "SVG and compile.json were written and independently structurally checked, rendered and analyzed", "fix": "Consumer runner sets PYTHONIOENCODING=utf-8 and PYTHONUTF8=1 before later child commands", "original_evidence_preserved": True},
        "process_policy": {"subprocess_timeout_seconds": 45, "outer_watchdog_seconds": 180, "numerical_threads": 1, "persistent_processes_started": 0, "cleanup": "all one-shot child processes exited; after-inventory saved separately"},
    }
    save(OUT / "report.json", result)
    print(json.dumps({"profile_pair": "passed", "revisions": len(records), "visual": result["visual_review"]["status"], "full_icon_accepted": False}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run", "revise", "finalize"])
    parser.add_argument("--profile", choices=["short", "full"])
    parser.add_argument("--revision", default="r001")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "revise":
        revise()
    elif args.action == "finalize":
        finalize()
    else:
        run(args.profile, args.revision)
