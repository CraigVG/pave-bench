import json

from PIL import Image

from pavebench.cli import main
from pavebench.eval import evaluate_mask_prediction
from pavebench.schemas import Case, MaskPrediction


def test_evaluate_mask_prediction_scores_binary_mask():
    case = Case(
        case_id="demo",
        image_width=4,
        image_height=4,
        gt_boundary=[(0, 0), (4, 0), (4, 4), (0, 4)],
        gt_cutouts=[],
    )
    prediction = MaskPrediction(
        case_id="demo",
        task="semantic_mask",
        track="pure_segmentation",
        mask=[[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]],
    )

    result = evaluate_mask_prediction(case, prediction)

    assert result.iou == 1
    assert result.passed


def test_cli_scores_mask_path_prediction(tmp_path):
    case_path = tmp_path / "metadata.json"
    predictions_path = tmp_path / "predictions.jsonl"
    out_path = tmp_path / "scores.json"
    mask_path = tmp_path / "mask.png"

    case_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 4, "height": 4},
                "gold": {"boundary": [[0, 0], [4, 0], [4, 4], [0, 4]], "cutouts": []},
            }
        ),
        encoding="utf-8",
    )
    Image.new("L", (4, 4), 255).save(mask_path)
    predictions_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "task": "semantic_mask",
                "track": "pure_segmentation",
                "maskPath": "mask.png",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["score", "--case", str(case_path), "--predictions", str(predictions_path), "--out", str(out_path)]) == 0

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["summary"]["passes"] == 1
    assert report["results"][0]["iou"] == 1
