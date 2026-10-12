import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests import test_controller as controller


class ZoomButtonTests(unittest.TestCase):
    setUpClass = classmethod(controller.ControllerTests.setUpClass.__func__)
    setUp = controller.ControllerTests.setUp
    tearDown = controller.ControllerTests.tearDown

    def test_mouse_click_changes_zoom_and_requests_render(self):
        self.w.show()
        self.app.processEvents()
        old_request=self.w.render_id
        QTest.mouseClick(self.w.zoom_in, Qt.MouseButton.LeftButton)
        self.assertAlmostEqual(self.w.zoom.value(),1.1)
        self.assertAlmostEqual(self.w.viewer.transform().m11(),1.1)
        self.assertGreater(self.w.render_id,old_request)
        QTest.mouseClick(self.w.zoom_out, Qt.MouseButton.LeftButton)
        self.assertAlmostEqual(self.w.zoom.value(),1.0)

    def test_buttons_respect_limits(self):
        self.w.zoom.setValue(2.5)
        self.w.zoom_in.click()
        self.assertAlmostEqual(self.w.zoom.value(),2.5)
        self.w.zoom.setValue(.5)
        self.w.zoom_out.click()
        self.assertAlmostEqual(self.w.zoom.value(),.5)
