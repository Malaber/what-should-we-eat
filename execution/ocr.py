import sys
import os
import glob
import json
import Quartz
import Vision
from Cocoa import NSURL

def extract_text(image_path):
    input_url = NSURL.fileURLWithPath_(image_path)
    image_handler = Quartz.CGImageSourceCreateWithURL(input_url, None)
    if not image_handler:
        print(f"Error loading image: {image_path}", file=sys.stderr)
        return ""

    req = Vision.VNRecognizeTextRequest.alloc().init()
    # Use accurate recognition
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setUsesLanguageCorrection_(True)
    # req.setRecognitionLanguages_(["de-DE", "en-US"]) # if we needed specific languages, but auto works well.

    request_handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(input_url, None)

    success, error = request_handler.performRequests_error_([req], None)
    if not success:
        print(f"Error performing OCR on {image_path}: {error}", file=sys.stderr)
        return ""

    results = req.results()
    text = []
    for observation in results:
        text.append(observation.topCandidates_(1)[0].string())
    
    return "\n".join(text)

def main():
    resources_dir = "/Users/tobhuber/Projects/what-should-we-eat/resources"
    output_file = "/Users/tobhuber/Projects/what-should-we-eat/.tmp/ocr_results.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    heic_files = glob.glob(os.path.join(resources_dir, "*.HEIC"))
    print(f"Found {len(heic_files)} HEIC files.")
    
    results = {}
    for i, file_path in enumerate(heic_files):
        print(f"Processing ({i+1}/{len(heic_files)}): {os.path.basename(file_path)}")
        text = extract_text(file_path)
        results[os.path.basename(file_path)] = text
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Done. Wrote results to {output_file}")

if __name__ == "__main__":
    main()
