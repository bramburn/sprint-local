import os
import pytest
from tools import FileCreatorTool, FileEditorTool, FilePatcherTool

class TestFileTools:
    def test_file_creator(self, temp_dir):
        """
        Test the FileCreatorTool for creating a new file.
        """
        tool = FileCreatorTool()
        file_path = os.path.join(temp_dir, "new_file.txt")
        
        result = tool._run(file_path, "Hello, World!")
        
        assert "File created successfully" in result
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        assert content == "Hello, World!"

    def test_file_editor(self, test_file):
        """
        Test the FileEditorTool for editing an existing file.
        """
        tool = FileEditorTool()
        
        result = tool._run(test_file, "Updated content")
        
        assert "File edited successfully" in result
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == "Updated content"

    def test_file_editor_backup(self, test_file):
        """
        Test the FileEditorTool's backup functionality.
        """
        tool = FileEditorTool()
        
        result = tool._run(test_file, "Updated content", backup=True)
        
        assert "File edited successfully" in result
        assert "with backup" in result
        
        backup_path = f"{test_file}.bak"
        assert os.path.exists(backup_path)
        
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        
        assert backup_content == "Original content"

    def test_file_patcher(self, test_file):
        """
        Test the FilePatcherTool for applying a patch to a file.
        """
        tool = FilePatcherTool()
        
        patch_content = """--- {0}
+++ {0}
@@ -1 +1 @@
-Original content
+Patched content""".format(test_file)
        
        result = tool._run(test_file, patch_content)
        
        assert "File patched successfully" in result
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == "Patched content"

    def test_file_patcher_backup(self, test_file):
        """
        Test the FilePatcherTool's backup functionality.
        """
        tool = FilePatcherTool()
        
        patch_content = """--- {0}
+++ {0}
@@ -1 +1 @@
-Original content
+Patched content""".format(test_file)
        
        result = tool._run(test_file, patch_content, backup=True)
        
        assert "File patched successfully" in result
        assert "with backup" in result
        
        backup_path = f"{test_file}.bak"
        assert os.path.exists(backup_path)
        
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        
        assert backup_content == "Original content"

    def test_file_creator_invalid_path(self, temp_dir):
        """
        Test the FileCreatorTool with an invalid file path.
        """
        tool = FileCreatorTool()
        
        with pytest.raises(ValueError, match="Cannot create files outside the current project directory"):
            tool._run("/absolute/path/outside/project/file.txt", "Content")

    def test_file_editor_nonexistent_file(self, temp_dir):
        """
        Test the FileEditorTool with a non-existent file.
        """
        tool = FileEditorTool()
        non_existent_file = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(ValueError, match="File does not exist"):
            tool._run(non_existent_file, "New content")

    def test_file_patcher_invalid_patch(self, test_file):
        """
        Test the FilePatcherTool with an invalid patch.
        """
        tool = FilePatcherTool()
        
        with pytest.raises(ValueError, match="Invalid patch content format"):
            tool._run(test_file, "Invalid patch content")
