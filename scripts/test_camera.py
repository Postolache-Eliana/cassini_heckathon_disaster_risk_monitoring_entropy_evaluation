import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.camera import analyze_frame


def main():

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    candidates = [
        os.path.join(base_dir, "uploads", "test.jpg"),
        os.path.join(base_dir, "uploads", "test.jpeg"),
        os.path.join(base_dir, "backend", "uploads", "test.jpg"),
        os.path.join(base_dir, "backend", "uploads", "test.jpeg"),
    ]

    image_path = None

    for path in candidates:
        if os.path.exists(path):
            image_path = path
            break

    print("[TEST] Resolved image path:", image_path)

    if image_path is None:
        print("[ERROR] No image found")
        return

    result = analyze_frame(image_path)

    print("\n[RESULT]")
    print(result)


if __name__ == "__main__":
    main()