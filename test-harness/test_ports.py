"""
Unit tests for the ports module.
"""

import socket
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

from utils.ports import find_sequential_ports, _is_port_available, check_sequential_port_block, PortInfo, PortBlockCheckResult


class TestPortsModule(unittest.TestCase):
    """Test cases for the ports module."""

    def test_find_sequential_ports_single_port(self):
        """Test finding a single available port."""
        ports = find_sequential_ports(base=9000, count=1)
        self.assertEqual(len(ports), 1)
        self.assertGreaterEqual(ports[0], 9000)
        
        # Verify the port is actually available
        self.assertTrue(_is_port_available(ports[0], "0.0.0.0"))

    def test_find_sequential_ports_multiple_ports(self):
        """Test finding multiple sequential ports."""
        ports = find_sequential_ports(base=9100, count=3)
        self.assertEqual(len(ports), 3)
        
        # Verify ports are sequential
        for i in range(1, len(ports)):
            self.assertEqual(ports[i], ports[i-1] + 1)
        
        # Verify all ports are available
        for port in ports:
            self.assertTrue(_is_port_available(port, "0.0.0.0"))

    def test_find_sequential_ports_default_parameters(self):
        """Test function with default parameters."""
        ports = find_sequential_ports()
        self.assertEqual(len(ports), 1)
        self.assertGreaterEqual(ports[0], 8090)

    def test_find_sequential_ports_invalid_count(self):
        """Test that invalid count raises ValueError."""
        with self.assertRaises(ValueError):
            find_sequential_ports(count=0)
        
        with self.assertRaises(ValueError):
            find_sequential_ports(count=-1)

    def test_find_sequential_ports_with_occupied_ports(self):
        """Test finding ports when some are occupied."""
        # Create a server socket to occupy a port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9200))
            server_socket.listen(1)
            
            # Find ports starting from the occupied port
            ports = find_sequential_ports(base=9200, count=2)
            
            # Should skip the occupied port and find next available sequential ports
            self.assertEqual(len(ports), 2)
            self.assertNotEqual(ports[0], 9200)  # Should skip occupied port
            self.assertEqual(ports[1], ports[0] + 1)
            
        finally:
            server_socket.close()

    def test_find_sequential_ports_skips_partially_occupied_sequence(self):
        """Test that function skips sequences where not all ports are available."""
        # Occupy port 9301 (middle of a potential sequence)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9301))
            server_socket.listen(1)
            
            # Try to find 3 sequential ports starting from 9300
            ports = find_sequential_ports(base=9300, count=3)
            
            # Should skip the sequence [9300, 9301, 9302] and find next available
            self.assertEqual(len(ports), 3)
            self.assertNotIn(9301, ports)  # Should not include occupied port
            
            # Verify found ports are sequential
            for i in range(1, len(ports)):
                self.assertEqual(ports[i], ports[i-1] + 1)
                
        finally:
            server_socket.close()

    def test_is_port_available_free_port(self):
        """Test _is_port_available with a free port."""
        # Use a high port number that's likely to be free
        self.assertTrue(_is_port_available(9999, "0.0.0.0"))

    def test_is_port_available_occupied_port(self):
        """Test _is_port_available with an occupied port."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9400))
            server_socket.listen(1)
            
            # Port should be reported as not available
            self.assertFalse(_is_port_available(9400, "0.0.0.0"))
            
        finally:
            server_socket.close()

    def test_different_host_parameter(self):
        """Test function with different host parameter."""
        ports = find_sequential_ports(base=9500, count=1, host="127.0.0.1")
        self.assertEqual(len(ports), 1)
        self.assertTrue(_is_port_available(ports[0], "127.0.0.1"))

    def test_port_range_boundary(self):
        """Test behavior near port range boundaries."""
        # Test with high port numbers
        ports = find_sequential_ports(base=65500, count=2)
        self.assertEqual(len(ports), 2)
        self.assertLessEqual(ports[1], 65535)

    @patch('utils.ports._is_port_available')
    def test_runtime_error_when_no_ports_available(self, mock_is_available):
        """Test that RuntimeError is raised when no ports are available."""
        # Mock all ports as unavailable
        mock_is_available.return_value = False
        
        with self.assertRaises(RuntimeError) as context:
            find_sequential_ports(base=9600, count=1)
        
        self.assertIn("Unable to find", str(context.exception))

    @patch('utils.ports._is_port_available')
    def test_runtime_error_when_insufficient_sequential_ports(self, mock_is_available):
        """Test RuntimeError when insufficient sequential ports are available."""
        # Mock alternating availability (no 3 sequential ports available)
        mock_is_available.side_effect = lambda port, host: port % 2 == 0
        
        with self.assertRaises(RuntimeError) as context:
            find_sequential_ports(base=9700, count=3)
        
        self.assertIn("Unable to find 3 sequential available ports", str(context.exception))

    def test_integration_with_real_sockets(self):
        """Integration test using real socket operations."""
        # Find ports and then verify we can actually bind to them
        ports = find_sequential_ports(base=9800, count=2)
        
        sockets = []
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('0.0.0.0', port))
                sockets.append(sock)
            
            # All bindings should succeed
            self.assertEqual(len(sockets), 2)
            
        finally:
            for sock in sockets:
                sock.close()

    def test_concurrent_port_allocation(self):
        """Test that port allocation works correctly under concurrent access."""
        results = []
        
        def allocate_ports():
            try:
                ports = find_sequential_ports(base=10000, count=2)
                results.append(ports)
            except Exception as e:
                results.append(e)
        
        # Run multiple threads trying to allocate ports
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=allocate_ports)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All allocations should succeed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)


class TestPortBlockCheck(unittest.TestCase):
    """Test cases for the port block checking functionality."""

    def test_check_sequential_port_block_available(self):
        """Test checking an available port block."""
        result = check_sequential_port_block(base=9000, count=3)
        self.assertTrue(result.available)
        self.assertEqual(result.requested_range, (9000, 9002))
        self.assertEqual(len(result.busy_ports), 0)
        self.assertIsNone(result.error_message)

    def test_check_sequential_port_block_with_busy_port(self):
        """Test checking a port block with a busy port."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9100))
            server_socket.listen(1)

            result = check_sequential_port_block(base=9100, count=3)
            self.assertFalse(result.available)
            self.assertEqual(result.requested_range, (9100, 9102))
            self.assertEqual(len(result.busy_ports), 1)
            self.assertEqual(result.busy_ports[0].port, 9100)
            self.assertFalse(result.busy_ports[0].available)
            self.assertIn("9100 already in use", result.error_message)
            self.assertIn("Ports 9100-9102", result.error_message)

        finally:
            server_socket.close()

    def test_check_sequential_port_block_multiple_busy_ports(self):
        """Test checking a port block with multiple busy ports."""
        server_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket1.bind(('0.0.0.0', 9200))
            server_socket1.listen(1)
            server_socket2.bind(('0.0.0.0', 9202))
            server_socket2.listen(1)

            result = check_sequential_port_block(base=9200, count=3)
            self.assertFalse(result.available)
            self.assertEqual(result.requested_range, (9200, 9202))
            self.assertEqual(len(result.busy_ports), 2)
            
            busy_port_numbers = [port.port for port in result.busy_ports]
            self.assertIn(9200, busy_port_numbers)
            self.assertIn(9202, busy_port_numbers)
            
            self.assertIn("9200 already in use", result.error_message)
            self.assertIn("9202 already in use", result.error_message)

        finally:
            server_socket1.close()
            server_socket2.close()

    def test_check_sequential_port_block_single_port(self):
        """Test checking a single port."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9300))
            server_socket.listen(1)

            result = check_sequential_port_block(base=9300, count=1)
            self.assertFalse(result.available)
            self.assertEqual(result.requested_range, (9300, 9300))
            self.assertEqual(len(result.busy_ports), 1)
            self.assertIn("Port 9300", result.error_message)
            self.assertNotIn("Ports", result.error_message)  # Should use singular "Port"

        finally:
            server_socket.close()

    def test_check_sequential_port_block_exceeds_max_port(self):
        """Test checking a port block that exceeds maximum port number."""
        result = check_sequential_port_block(base=65534, count=4)
        self.assertFalse(result.available)
        self.assertEqual(result.requested_range, (65534, 65537))
        self.assertEqual(len(result.busy_ports), 0)
        self.assertIn("exceeds maximum port number", result.error_message)

    def test_check_sequential_port_block_invalid_count(self):
        """Test that invalid count returns appropriate error."""
        result = check_sequential_port_block(base=9000, count=0)
        self.assertFalse(result.available)
        self.assertEqual(result.requested_range, (9000, 8999))
        self.assertEqual(len(result.busy_ports), 0)
        self.assertIn("Count must be at least 1", result.error_message)

        result = check_sequential_port_block(base=9000, count=-1)
        self.assertFalse(result.available)
        self.assertIn("Count must be at least 1", result.error_message)

    def test_check_sequential_port_block_different_host(self):
        """Test checking port block with different host parameter."""
        result = check_sequential_port_block(base=9400, count=2, host="127.0.0.1")
        self.assertTrue(result.available)
        self.assertEqual(result.requested_range, (9400, 9401))
        self.assertEqual(len(result.busy_ports), 0)

    def test_port_info_process_info(self):
        """Test that PortInfo includes process information when available."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(('0.0.0.0', 9500))
            server_socket.listen(1)

            result = check_sequential_port_block(base=9500, count=1)
            self.assertFalse(result.available)
            self.assertEqual(len(result.busy_ports), 1)
            
            port_info = result.busy_ports[0]
            self.assertEqual(port_info.port, 9500)
            self.assertFalse(port_info.available)
            # Process info should be present (may be "unknown process" if detection fails)
            self.assertIsNotNone(port_info.process_info)
            self.assertIn("process", port_info.process_info)

        finally:
            server_socket.close()


if __name__ == '__main__':
    unittest.main()
