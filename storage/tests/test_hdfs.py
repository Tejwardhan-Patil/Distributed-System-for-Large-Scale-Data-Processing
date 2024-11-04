import unittest
from hdfs import InsecureClient
from unittest.mock import patch, MagicMock
import os

# HDFS Client URL and paths
HDFS_URL = "http://localhost:9870"
HDFS_PATH = "/data/test/"
LOCAL_PATH = "/tmp/test/"

class TestHDFSStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = InsecureClient(HDFS_URL)

    def setUp(self):
        self.mock_client = patch('hdfs.InsecureClient', autospec=True).start()
        self.addCleanup(patch.stopall)

    def test_hdfs_connection(self):
        """Test that HDFS client establishes a connection to the correct URL"""
        self.mock_client.assert_called_with(HDFS_URL)

    def test_hdfs_mkdir(self):
        """Test directory creation in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.makedirs.return_value = True

        result = client_instance.makedirs(HDFS_PATH)
        self.assertTrue(result)
        client_instance.makedirs.assert_called_with(HDFS_PATH)

    def test_hdfs_list_files(self):
        """Test listing files in an HDFS directory"""
        client_instance = self.mock_client.return_value
        client_instance.list.return_value = ['file1.txt', 'file2.txt']

        files = client_instance.list(HDFS_PATH)
        self.assertEqual(files, ['file1.txt', 'file2.txt'])
        client_instance.list.assert_called_with(HDFS_PATH)

    def test_hdfs_upload(self):
        """Test uploading a file to HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.upload.return_value = True

        result = client_instance.upload(HDFS_PATH + 'file1.txt', LOCAL_PATH + 'file1.txt')
        self.assertTrue(result)
        client_instance.upload.assert_called_with(HDFS_PATH + 'file1.txt', LOCAL_PATH + 'file1.txt')

    def test_hdfs_download(self):
        """Test downloading a file from HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.download.return_value = True

        result = client_instance.download(HDFS_PATH + 'file1.txt', LOCAL_PATH + 'file1.txt')
        self.assertTrue(result)
        client_instance.download.assert_called_with(HDFS_PATH + 'file1.txt', LOCAL_PATH + 'file1.txt')

    def test_hdfs_read_file(self):
        """Test reading a file from HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.read.return_value = b'Hello World'

        data = client_instance.read(HDFS_PATH + 'file1.txt')
        self.assertEqual(data, b'Hello World')
        client_instance.read.assert_called_with(HDFS_PATH + 'file1.txt')

    def test_hdfs_delete_file(self):
        """Test deleting a file from HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.delete.return_value = True

        result = client_instance.delete(HDFS_PATH + 'file1.txt')
        self.assertTrue(result)
        client_instance.delete.assert_called_with(HDFS_PATH + 'file1.txt')

    def test_hdfs_move_file(self):
        """Test moving a file within HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.rename.return_value = True

        result = client_instance.rename(HDFS_PATH + 'file1.txt', HDFS_PATH + 'file1_moved.txt')
        self.assertTrue(result)
        client_instance.rename.assert_called_with(HDFS_PATH + 'file1.txt', HDFS_PATH + 'file1_moved.txt')

    def test_hdfs_file_exists(self):
        """Test checking if a file exists in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.status.return_value = {'type': 'FILE'}

        file_status = client_instance.status(HDFS_PATH + 'file1.txt', strict=False)
        self.assertEqual(file_status['type'], 'FILE')
        client_instance.status.assert_called_with(HDFS_PATH + 'file1.txt', strict=False)

    def test_hdfs_get_file_size(self):
        """Test retrieving file size from HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.status.return_value = {'length': 1024}

        file_status = client_instance.status(HDFS_PATH + 'file1.txt', strict=False)
        self.assertEqual(file_status['length'], 1024)
        client_instance.status.assert_called_with(HDFS_PATH + 'file1.txt', strict=False)

    def test_hdfs_change_permissions(self):
        """Test changing file permissions in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.set_permission.return_value = True

        result = client_instance.set_permission(HDFS_PATH + 'file1.txt', '755')
        self.assertTrue(result)
        client_instance.set_permission.assert_called_with(HDFS_PATH + 'file1.txt', '755')

    def test_hdfs_get_file_block_size(self):
        """Test getting block size of a file in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.status.return_value = {'blockSize': 134217728}

        block_size = client_instance.status(HDFS_PATH + 'file1.txt', strict=False)['blockSize']
        self.assertEqual(block_size, 134217728)
        client_instance.status.assert_called_with(HDFS_PATH + 'file1.txt', strict=False)

    def test_hdfs_append_data(self):
        """Test appending data to an HDFS file"""
        client_instance = self.mock_client.return_value
        mock_file = MagicMock()
        mock_file.write.return_value = 11
        client_instance.append.return_value.__enter__.return_value = mock_file

        with client_instance.append(HDFS_PATH + 'file1.txt') as file:
            file.write(b'Appended data')

        mock_file.write.assert_called_with(b'Appended data')

    def test_hdfs_replication_factor(self):
        """Test changing replication factor of a file in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.set_replication.return_value = True

        result = client_instance.set_replication(HDFS_PATH + 'file1.txt', 3)
        self.assertTrue(result)
        client_instance.set_replication.assert_called_with(HDFS_PATH + 'file1.txt', 3)

    def test_hdfs_checksum_verification(self):
        """Test verifying the checksum of a file in HDFS"""
        client_instance = self.mock_client.return_value
        client_instance.checksum.return_value = {'algorithm': 'MD5', 'value': 'a1b2c3d4'}

        checksum = client_instance.checksum(HDFS_PATH + 'file1.txt')
        self.assertEqual(checksum['value'], 'a1b2c3d4')
        client_instance.checksum.assert_called_with(HDFS_PATH + 'file1.txt')


if __name__ == '__main__':
    unittest.main()