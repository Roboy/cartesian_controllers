#!/usr/bin/env python
# - BEGIN LICENSE BLOCK -------------------------------------------------------
# - END LICENSE BLOCK ---------------------------------------------------------

# -----------------------------------------------------------------------------
# \file    moving_target.py
#
# \author  Stefan Scherzinger <scherzin@fzi.de>
# \date    2018/09/12
#
# -----------------------------------------------------------------------------

# ROS
import rospy
from geometry_msgs.msg import Pose, PoseStamped
from interactive_markers.interactive_marker_server import *
from interactive_markers.menu_handler import *
from visualization_msgs.msg import *

# Other
import numpy as np
import copy

class MovingTarget(object):
    """ Turn a TF frame into a moving target for CartesianMotionControllers

    This class creates an interactive marker to a (possibly moving) TF frame
    and publishes its pose as a PoseStamped with respect to a specified robot
    base. Its principal application is to create dynamic targets for
    CartesianMotionControllers, since they cannot follow TFs directly. The user
    can adjust offsets manually with the drag-and-drop marker in RViz.

    On startup, the marker coincides with the specified robot end-effector to
    prevent jumps in the CartesianMotionControllers. The marker can be reset
    to the robot end-effector at all times via the 'reset' service call.
    """

    def __init__(self):
        rospy.init_node('moving_target', anonymous=True)

        # Configuration
        self.robot_base = rospy.get_param('~robot_base_link')
        self.end_effector = rospy.get_param('~end_effector_link')
        self.moving_tf_frame = rospy.get_param('~moving_tf_frame')
        self.target_frame_topic = rospy.get_param('~target_frame_topic')

        # Startup
        starting_pose = self.get_end_effector_pose()
        self.marker = self.make_interactive_marker(self.moving_tf_frame, starting_pose)

        self.server = InteractiveMarkerServer("moving_target")
        self.server.insert(self.marker, self.process_marker_feedback)
        self.server.applyChanges()

    def process_marker_feedback(self, feedback):
        pass

    def add_marker_visualization(self, marker, scale):
        # Create a sphere as a handle
        visual = Marker()
        visual.type = Marker.SPHERE
        visual.scale.x = scale  # bounding box in meter
        visual.scale.y = scale
        visual.scale.z = scale
        visual.color.r = 1.0  # orange
        visual.color.g = 0.5
        visual.color.b = 0.0
        visual.color.a = 1.0

        # Create a non-interactive control for the appearance
        visual_control = InteractiveMarkerControl()
        visual_control.always_visible = True
        visual_control.markers.append(visual)
        marker.controls.append(visual_control)

    def add_axis_control(self, marker, axis):
        control = InteractiveMarkerControl()
        norm = np.linalg.norm(axis)
        if norm == 0:
            return
        control.orientation.w = 1 / norm
        control.orientation.x = axis[0] / norm
        control.orientation.y = axis[1] / norm
        control.orientation.z = axis[2] / norm

        control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
        marker.controls.append(copy.deepcopy(control))
        control.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
        marker.controls.append(copy.deepcopy(control))

    def prepare_marker_controls(self, marker):
        # Add colored sphere as visualization
        self.add_marker_visualization(marker, 0.05)

        # Create move and rotate controls along all axis
        self.add_axis_control(marker, [1, 0, 0]);
        self.add_axis_control(marker, [0, 1, 0]);
        self.add_axis_control(marker, [0, 0, 1]);

    def get_end_effector_pose(self):
        pose = Pose()
        return pose

    def make_interactive_marker(self, tf_reference_frame, starting_pose):

        marker = InteractiveMarker()
        marker.header.frame_id = tf_reference_frame
        marker.header.stamp = rospy.Time(0)
        marker.pose = starting_pose
        marker.scale = 0.1
        marker.name = "moving_offset"
        marker.description = "Follow {} with an offset".format(tf_reference_frame)

        self.prepare_marker_controls(marker)
        return marker

if __name__ == '__main__':
    _ = MovingTarget()
    try:
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
