import errno
import os
import os.path
import shutil
import subprocess
from threading import Thread


def get_ghostscript_path():
    gs_names = ['gs', 'gswin32', 'gswin64']
    for name in gs_names:
        if shutil.which(name):
            return shutil.which(name)
    raise FileNotFoundError(f'No GhostScript executable was found on path ({"/".join(gs_names)})')


def get_size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def compress_file(input_file_path: str, output_file_path: str, power: int = 2):
    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    color_image_resolution = 200
    gray_image_resolution = 200
    mono_image_resolution = 200

    gs = get_ghostscript_path()
    initial_size = os.path.getsize(input_file_path)
    subprocess.run([gs, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.5',
                    f'-dPDFSETTINGS={quality[power]}',
                    '-dAutoRotatePages=/None',
                    '-dColorConversionStrategy=/RGB',
                    '-dNOPAUSE', '-dBATCH', '-dQUIET',
                    '-dCompressPages=true', '-dCompressFonts=true',
                    '-dDetectDuplicateImages=true',
                    '-dDownsampleColorImages=true', '-dDownsampleGrayImages=true',
                    '-dDownsampleMonoImages=true',
                    f'-dColorImageResolution={color_image_resolution}',
                    f'-dGrayImageResolution={gray_image_resolution}',
                    f'-dMonoImageResolution={mono_image_resolution}',
                    '-dDoThumbnails=false',
                    '-dCreateJobTicket=false',
                    '-dPreserveEPSInfo=false',
                    '-dPreserveOPIComments=false',
                    '-dPreserveOverprintSettings=false',
                    '-dUCRandBGInfo=/Remove',
                    f'-sOutputFile={output_file_path}',
                    input_file_path],
                   check=True
                   )
    final_size = os.path.getsize(output_file_path)
    ratio = 1 - (final_size / initial_size)
    print("Compression by {0:.2%}.".format(ratio))


def batch_optimize(input_dir: str):
    output_dir = f"{input_dir}_optimized"
    if not os.path.exists(input_dir):
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), input_dir)
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(
            errno.ENOTDIR, os.strerror(errno.ENOTDIR), input_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    threads = [Thread(target=compress_file, args=(
        os.path.join(input_dir, pdffile),
        os.path.join(output_dir, pdffile)
    )) for pdffile in os.listdir(input_dir)]

    num_threads = 7
    batch = list()

    for i, thread in enumerate(threads):
        if len(batch) == num_threads or i == len(threads) - 1:
            for b in batch:
                b.start()
            for b in batch:
                b.join()
            batch = list()
        elif len(batch) < num_threads:
            batch.append(thread)


if __name__ == '__main__':
    batch_optimize('/projects/certificates')
