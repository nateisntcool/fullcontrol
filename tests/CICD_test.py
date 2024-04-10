from datetime import datetime
import subprocess, difflib, os
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os


# usage: run this script in the tests directory with 'python CICD_test.py'
# this script runs all the tutorials in the combined_tutorials.py file, which is generated by the tutorials_to_py.py script in the bin directory
# it saves the printouts to test_print_output.txt, and compares them to the reference printouts in test_print_output_reference.txt
# the results of the tests are saved to test_result.txt
# it also collates all the images generated by the tutorials into a single image collage.png, and cleans up after itself by deleting all the generated temporary files
# the user should confirm that the collage.png looks the same as collage_reference.png

def run_tutorials():
    # Read the script as a list of lines
    with open('combined_tutorials.py', 'r') as file: script = file.readlines()
    # Add 'import sys' at the beginning and update the script lines with progress updates
    script = ['import sys\n'] + [
        f'sys.stderr.write("Progress: {int(i / len(script) * 100)}%\\n")\n{line}' if line == '# In[ ]:\n' else line
        for i, line in enumerate(script)
    ]
    # Write the modified script to a temporary file, run it, then delete it
    with open('temp.py', 'w') as file: file.write(''.join(script))
    try:
        with open('test_print_output.txt', 'w') as f: subprocess.run(['python', 'temp.py'], stdout=f, check=True)
        os.remove('temp.py')
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running combined_tutorials.py (temporarily saved as temp.py with minor changes): {e}")
        exit()

def compare_files(file1, file2, str_result):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        text1 = f1.readlines()
        text2 = f2.readlines()
    differences = list(difflib.ndiff(text1, text2))
    differences = [line for line in differences if line.startswith('- ') or line.startswith('+ ')] # get rid of excess lines of into about differences
    if differences:
        str_result.append(f"warning: {len(differences)} differences found between tutorial printouts now and the reference printouts - unless differences are expected or explainable (e.g. tutorials changes; e.g. printout order for non-ordered sets/dictionaries), they may cause a pull request to be rejected")
        print(str_result[-1])
        str_result.append(''.join(differences))
        user_input = input("\ndo you want the differences to be printed out here? (y/n):")
        if user_input.lower() == "y": print(str_result[-1])
    else:
        str_result.append("great! no differences found between tutorial printouts now and the reference printouts.")
        print(str_result[-1])

def collage_all_images():
    # Open all .png files in the current directory
    png_files = [f for f in os.listdir('.') if f.endswith('.png') and f not in ['collage.png', 'collage_reference.png']]
    images = [Image.open(f) for f in png_files]
    images.sort(key=lambda img: img.filename)
    width, height = 200, 125
    num_rows  = int(len(images) ** 0.5)
    num_cols = (len(images) + num_rows - 1) // num_rows
    # Resize all images to the minimum size
    images = [img.resize((width, height)) for img in images]
    # Create a new image with a size large enough to fit all the images
    collage_width, collage_height = width * num_cols, height * num_rows
    collage = Image.new('RGBA', (collage_width, collage_height))
    # Paste each image into the collage
    for i, img in enumerate(images):
        row, col = i // num_cols, i % num_cols
        collage.paste(img, (col * width, row * height))
    # Add watermark with date and time
    watermark_position = (collage_width - 150, collage_height - 20)
    draw = ImageDraw.Draw(collage)
    draw.text(watermark_position, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(255, 255, 255, 128))
    collage.save('collage.png')

def delete_redundant_files():
    temp_files = [f for f in os.listdir('.') if f.endswith(('.png', '.gcode', '.json', '.stl'))]
    for f in temp_files:
        if f not in ['collage.png', 'collage_reference.png']:
            os.remove(f)


os.environ['FULLCONTROL_CICD_TESTING'] = 'True'
str_result = [datetime.now().strftime("test results generated %d-%m-%Y__%H-%M-%S\n")]
print('tests may take a few minutes - images and printouts from all tutorial notebooks are being generated')
print('if an error occurs, check the error message and consider debugging with the original tutorial notebook rather than via this script.')
print("if you've changed one of the tutorial notebooks, you'll need to run tutorials_to_py.py in the bin directory to update combined_tutorials.py.")
run_tutorials()
del os.environ['FULLCONTROL_CICD_TESTING']
compare_files('test_print_output.txt','test_print_output_reference.txt', str_result)
collage_all_images()
delete_redundant_files()
print('figures generated by the notebooks have been collated in tests/collage.png\ntest results saved to test_result.txt')
print('\nplease confirm that collage.png looks the same as collage_reference.png in your pull-request comment')
with open('test_result.txt', 'w') as file: file.write('\n'.join(str_result))
