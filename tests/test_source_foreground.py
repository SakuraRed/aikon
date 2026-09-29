"""Semantic controls for a uniform-background source mask, not score fitting."""
import unittest
import numpy as np
from tools.source_foreground import exterior_foreground


class SourceForegroundTests(unittest.TestCase):
    def source(self):
        a=np.full((64,64,4),(15,15,15,255),dtype=np.uint8)
        a[8:56,8:56,:3]=(90,120,190)
        return a

    def test_enclosed_backdrop_colored_eye_remains_foreground(self):
        a=self.source();a[25:35,25:35,:3]=(15,15,15)
        mask,_=exterior_foreground(a)
        self.assertTrue(mask[30,30]);self.assertEqual(int(mask.sum()),48*48)

    def test_connected_backdrop_notch_remains_outside(self):
        a=self.source();a[:32,28:36,:3]=(15,15,15)
        mask,_=exterior_foreground(a)
        self.assertFalse(mask[20,30]);self.assertTrue(mask[35,30])

    def test_real_transparent_inner_hole_is_preserved(self):
        a=self.source();a[25:35,25:35,3]=0
        mask,_=exterior_foreground(a)
        self.assertFalse(mask[30,30]);self.assertEqual(int(mask.sum()),48*48-100)

    def test_alpha_zero_rgb_does_not_invent_foreground(self):
        a=self.source();a[:4,:,:3]=255;a[:4,:,3]=0
        mask,_=exterior_foreground(a)
        self.assertFalse(mask[:4].any())

    def test_clipped_blue_subject_at_canvas_edge_is_retained(self):
        a=self.source();a[20:40,:16,:3]=(90,120,190)
        mask,_=exterior_foreground(a)
        self.assertTrue(mask[25,0]);self.assertFalse(mask[5,0])

    def test_color_indistinguishable_from_exterior_is_not_claimed_recoverable(self):
        a=self.source();a[20:40,:32,:3]=(15,15,15)
        mask,_=exterior_foreground(a)
        self.assertFalse(mask[25,20])

    def test_invalid_inputs_do_not_silently_change_scale_or_dtype(self):
        for data in (self.source().astype(float),self.source()[:,:,:3]):
            with self.assertRaises(ValueError):exterior_foreground(data)


if __name__=='__main__':unittest.main()
