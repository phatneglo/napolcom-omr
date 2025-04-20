"""
This script is used to save the example images from the system clipboard.
You can manually save the images from your conversation with Claude, then run this script.

Instructions:
1. Right-click on each image in the conversation
2. Select "Save image as..." and save to the samples directory
3. Name them sample1.jpg, sample2.jpg, etc.
"""

import os
import sys

def main():
    print("Please save the sample images manually to the samples directory.")
    print("You can right-click on the images in the conversation and select 'Save image as...'")
    print("Save them as:")
    print("  - samples/sample1.jpg")
    print("  - samples/sample2.jpg")
    
    if not os.path.exists("samples"):
        print("Creating samples directory...")
        os.makedirs("samples")
    
    print("\nAfter saving the images, you can run the OMR parser on them with:")
    print("  python main.py samples/*.jpg --out results.csv")
    print("Or start the web interface with:")
    print("  python api.py")

if __name__ == "__main__":
    main()
