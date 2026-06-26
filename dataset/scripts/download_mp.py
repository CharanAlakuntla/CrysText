"""
Download CIF files from Materials Project using mp-api.
Usage:
    pip install mp-api
    python download_mp.py --api-key YOUR_MP_API_KEY --count 1000

Get a free API key at: https://next.materialsproject.org/api
"""
import argparse
import os
import time

def download(api_key: str, count: int, output_dir: str):
    try:
        from mp_api.client import MPRester
    except ImportError:
        print("Install mp-api first: pip install mp-api")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Connecting to Materials Project...")

    with MPRester(api_key) as mpr:
        docs = mpr.materials.summary.search(
            fields=["material_id", "formula_pretty"],
            num_chunks=count // 100 + 1,
            chunk_size=100,
        )
        downloaded = 0
        for doc in docs[:count]:
            mid = doc.material_id
            formula = doc.formula_pretty.replace("/", "-")
            out_path = os.path.join(output_dir, f"{formula}_{mid}.cif")
            if os.path.exists(out_path):
                continue
            try:
                structure = mpr.get_structure_by_material_id(mid)
                structure.to(fmt="cif", filename=out_path)
                downloaded += 1
                if downloaded % 50 == 0:
                    print(f"  Downloaded {downloaded}/{count}")
                time.sleep(0.1)
            except Exception as e:
                print(f"  Skipped {mid}: {e}")

    print(f"\nDone. Downloaded {downloaded} CIF files to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output-dir", default=os.path.join(os.path.dirname(__file__), "..", "cif_files"))
    args = parser.parse_args()
    download(args.api_key, args.count, os.path.abspath(args.output_dir))
