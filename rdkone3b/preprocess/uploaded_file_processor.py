
import os
import shutil
import tarfile
from rdkone3b.utils.constants import UPLOAD_DIRECTORY

class UPloadedFilesProcessor():
    """Processor for handling uploaded files in the application."""
    def __init__(self, path: str = UPLOAD_DIRECTORY):
        self.path = path
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def process_uploaded_files(self):
        """Process uploaded files by extracting and merging logs."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Upload directory '{self.path}' does not exist.")
        
        # Create a temporary directory for extraction
        temp_dir = os.path.join(self.path, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        for file in os.listdir(self.path):
            filename = file.lower()
            if filename.endswith(".tgz") or filename.endswith(".tar.gz"):
                src_file = os.path.join(self.path, file)
                base = file.rsplit('.', 2)[0]
                dest = os.path.join(temp_dir, base)
                os.makedirs(dest, exist_ok=True)
                with tarfile.open(src_file, "r:gz") as tar:
                    tar.extractall(path=dest)
        
        self._merge_files(temp_dir, output_dir=os.path.join(self.path, "merged_logs"))
        self._clean_temp_files(input_dir=temp_dir)

    def _merge_files(self,temp_dir, output_dir="./merged_logs"):
        os.makedirs(output_dir, exist_ok=True)
        folder_path = temp_dir
        folders = os.listdir(folder_path)
        folders.sort()

        for dirname in folders:
            content = os.path.join(folder_path, dirname)
            dirs = os.listdir(content)
            if len(dirs) == 1:
                for inner_dirname in dirs:
                    in_path = os.path.join(content, inner_dirname)
            else:
                in_path = content

            for in_filename in os.listdir(in_path):
                if (
                    "2023" not in in_filename
                    and "2024" not in in_filename
                    and "2025" not in in_filename
                ):
                    out_filename = in_filename
                else:
                    out_filename = in_filename[19:]
                    if "024-" in out_filename:
                        out_filename = in_filename[37:]
                    if "1_" in out_filename:
                        out_filename = out_filename[2:]
                    if out_filename and out_filename[0] in "0123456789_":
                        out_filename = out_filename[1:]

                out_file = os.path.join(output_dir, out_filename)
                in_file = os.path.join(in_path, in_filename)

                with open(in_file, "rb") as rd, open(out_file, "ab") as wr:
                    message = "****Merging " + in_file + " **********\n"
                    wr.write(message.encode("utf-8"))
                    shutil.copyfileobj(rd, wr)

    def _clean_temp_files(self,input_dir):
        for name in os.listdir(input_dir):
            full_path = os.path.join(input_dir, name)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
        os.rmdir(input_dir)
        print(f"Cleaned all contents from {input_dir}")

