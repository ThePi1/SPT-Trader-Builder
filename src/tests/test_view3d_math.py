"""The 3D view's maths, without a screen: triangles and what a click hits, the camera, and dragging a zone's handles."""

import math

import numpy as np
import pytest

from maps import geometry as G
from maps.navmesh import NavMesh
from maps.triangles import Triangles, box_edges, box_faces, pick_box, ray_box
from ui.view3d import handles as H
from ui.view3d.camera import Camera


def two_floors():
	"""A 10 x 10 m floor at height 0 and a 4 x 4 m one above it at 3 m (a square polygon each)."""
	vertices = [(0, 0, 0), (10, 0, 0), (10, 0, 10), (0, 0, 10), (3, 3, 3), (7, 3, 3), (7, 3, 7), (3, 3, 7)]
	return NavMesh(vertices, [((0, 3, 2, 1), 0), ((4, 7, 6, 5), 0)])


def test_the_navmesh_is_cut_into_triangles_whose_normals_point_up():
	tri = Triangles.from_navmesh(two_floors())
	assert len(tri) == 4 and tri.bounds() == ((0, 0, 0), (10, 3, 10))
	assert np.allclose(tri.normals(), [(0, 1, 0)] * 4)
	assert tri.vertex_array().shape == (12, 3)


def test_a_click_hits_the_first_floor_and_the_cut_hides_what_is_above():
	tri = Triangles.from_navmesh(two_floors())
	hit = tri.pick((5, 20, 5), (0, -1, 0))
	assert hit.point == pytest.approx((5, 3, 5)) and hit.distance == pytest.approx(17)
	assert tri.pick((5, 20, 5), (0, -1, 0), below=2.0).point == pytest.approx((5, 0, 5))  # (the upper floor is cut away)
	assert tri.pick((1, 20, 1), (0, -1, 0)).point == pytest.approx((1, 0, 1))  # (beside the upper floor)
	assert tri.pick((50, 20, 50), (0, -1, 0)) is None
	slanted = tri.pick((-5, 5, 5), _unit((1, -0.5, 0)))
	assert slanted.point == pytest.approx((5, 0, 5))


def test_rays_and_boxes():
	box = G.Box((0, 1, 0), (2, 2, 4), G.yaw_rotation(90))  # (turned: 4 m along x, 2 m along z)
	assert ray_box((-10, 1, 0), (1, 0, 0), box) == pytest.approx(8)
	assert ray_box((0, 1, -10), (0, 0, 1), box) == pytest.approx(9)
	assert ray_box((0, 1, 0), (1, 0, 0), box) == 0.0  # (from inside)
	assert ray_box((-10, 5, 0), (1, 0, 0), box) is None
	other = G.Box((5, 1, 0), (1, 1, 1))
	assert pick_box((-10, 1, 0), (1, 0, 0), [other, box]).index == 1
	assert box_faces(box).shape == (36, 3) and box_edges(box).shape == (24, 3)


def _unit(v):
	n = math.sqrt(sum(c * c for c in v))
	return tuple(c / n for c in v)


def test_the_camera_shows_east_on_the_right_and_north_up_from_above():
	cam = Camera(target=(100, 0, 50), distance=40, top_down=True)
	cx, cy = cam.project((100, 0, 50), 800, 600)
	assert (cx, cy) == pytest.approx((400, 300))
	east = cam.project((110, 0, 50), 800, 600)
	north = cam.project((100, 0, 60), 800, 600)
	assert east[0] > cx and east[1] == pytest.approx(cy)
	assert north[1] < cy and north[0] == pytest.approx(cx)


def test_the_ray_under_a_pixel_goes_through_what_is_drawn_there():
	for cam in (Camera(target=(10, 2, -5), yaw=30, pitch=40, distance=25), Camera(target=(10, 2, -5), yaw=200, distance=25, top_down=True)):
		point = (14.0, 0.5, -2.0)
		px, py = cam.project(point, 640, 480)
		origin, direction = cam.ray(px, py, 640, 480)
		to_point = np.subtract(point, origin)
		along = float(np.dot(to_point, direction))
		assert np.linalg.norm(to_point - along * np.asarray(direction)) < 1e-6
		pixels, front = cam.project_many([point, (-3.0, 1.0, 7.0), cam.eye()], 640, 480)  # (many at once, as the view draws the floor spots)
		assert pixels[0] == pytest.approx((px, py)) and pixels[1] == pytest.approx(cam.project((-3.0, 1.0, 7.0), 640, 480))
		if not cam.top_down:  # (seen straight down from far above, nothing is behind the camera)
			assert front.tolist() == [True, True, False] and cam.project(cam.eye(), 640, 480) is None
		origin, direction = cam.ray(320, 240, 640, 480)  # (the middle of the view looks at the target)
		to_target = np.subtract(cam.target, origin)
		assert np.linalg.norm(to_target - float(np.dot(to_target, direction)) * np.asarray(direction)) < 1e-6


def test_the_camera_orbits_pans_zooms_and_frames():
	cam = Camera(target=(0, 0, 0), yaw=0, pitch=45, distance=50)
	cam.orbit(90, 100)
	assert cam.yaw == 90 and cam.pitch == 89.5
	top = Camera(target=(0, 0, 0), distance=50, top_down=True)
	before = top.project((5, 0, 5), 800, 600)
	top.pan(40, -30, 600)  # (drag right and up: the map follows the mouse)
	after = top.project((5, 0, 5), 800, 600)
	assert after == pytest.approx((before[0] + 40, before[1] - 30))
	cam = Camera(target=(0, 0, 0), distance=100)
	cam.zoom(0.5, toward=(10, 0, 0))
	assert cam.distance == 50 and cam.target == pytest.approx((5, 0, 0))
	cam.frame((0, 0, 0), (10, 4, 20))
	assert cam.target == pytest.approx((5, 2, 10)) and cam.distance > 20


def test_dragging_the_handles_of_a_zone():
	box = G.Box((0, 1, 0), (4, 2, 6))
	spots = {(h.kind, h.axis, h.side): h for h in H.handles(box)}
	assert spots[(H.SIZE, 0, 1)].position == pytest.approx((2, 1, 0)) and spots[(H.TURN, -1, 0)].position == pytest.approx((0, 0, 4.5))
	down = (0, -1, 0)

	drag = H.Drag(box, H.MOVE, (1, 10, 1), down, grab=(1, 2, 1))  # (the mouse goes down on the top of the box)
	moved = drag.box_at((4, 10, -2), down)
	assert moved.center == pytest.approx((3, 1, -3)) and moved.size == box.size

	face = spots[(H.SIZE, 0, 1)]
	drag = H.Drag(box, H.SIZE, (2, 10, 0), down, handle=face)
	wider = drag.box_at((3.5, 10, 0), down)  # (the +x face goes out 1.5 m; the -x face stays at -2)
	assert wider.size == pytest.approx((5.5, 2, 6)) and wider.center == pytest.approx((0.75, 1, 0))
	assert drag.box_at((-9, 10, 0), down).size[0] == H.SMALLEST

	lift = spots[(H.LIFT, -1, 0)]
	side = (1, 0, 0)
	drag = H.Drag(box, H.LIFT, (-10, lift.position[1], 0), side, handle=lift)
	assert drag.box_at((-10, lift.position[1] + 0.8, 0), side).center == pytest.approx((0, 1.8, 0))
	assert drag.box_at((-10, lift.position[1] + 0.8, 0), side, snap=True).center[1] == pytest.approx(1.75)  # (its bottom, 0.8 m, snapped to 0.75)

	turn = spots[(H.TURN, -1, 0)]
	drag = H.Drag(box, H.TURN, (0, 10, 4.5), down, handle=turn)
	turned = drag.box_at((4.5, 10, 0), down)  # (the handle taken from north round to east: a quarter turn clockwise)
	assert G.yaw_of(turned.rotation) == pytest.approx(90)
	assert G.yaw_of(drag.box_at((4.5, 10, 1.0), down, snap=True).rotation) == pytest.approx(75)


def test_a_tilted_box_has_no_turn_handle():
	tilted = G.Box((0, 0, 0), (1, 1, 1), G.q_normalize((0.3, 0.0, 0.0, 0.95)))
	assert H.TURN not in {h.kind for h in H.handles(tilted)}
