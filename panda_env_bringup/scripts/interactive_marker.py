#!/usr/bin/env python

import rospy
from tf2_ros import TransformBroadcaster

from copy import copy
from interactive_markers.interactive_marker_server import *
from interactive_markers.menu_handler import *
from visualization_msgs.msg import *
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Pose, Quaternion, Vector3, TwistStamped
from std_msgs.msg import ColorRGBA

import numpy as np
from math import pi


OBJECT_FRAME = "panda_hand"
OBJECT_ID = "sphere"
DIM_X = 0.1
DIM_Y = 0.1
DIM_Z = 0.2
ODOM_UPDATE_RATE = 1000 #Hz

def get_object_marker():
    marker = Marker()
    marker.type = Marker.SPHERE
    marker.header.frame_id = OBJECT_FRAME
    marker.scale.x = 0.05
    marker.scale.y = 0.05
    marker.scale.z = 0.05
    return copy(marker)

# interactive marker controls
class InteractiveControls:

    def __init__(self,
                 object_marker,
                 server= None,
                 menu_handler = None,
                 on_move_callback = None,
                 reference_frame = OBJECT_FRAME,
                 object_id = OBJECT_ID,
                 object_pose = Pose(Point(0, 0, 0), Quaternion(0.0, 0.0, 0.0, 1.0)),
                 object_color = ColorRGBA(0.0,0.0,1.0,1.0)):

        self.server = InteractiveMarkerServer("object_controls") if server is None else server
        self.object_marker = object_marker
        self.reference_frame = reference_frame
        self.object_frame = object_id
        self.menu_handler = menu_handler
        self.on_move_callback = on_move_callback


        self.object_pose = object_pose
        self.object_color = object_color

    def set_menu_handler(self, menu_handler):
        self.menu_handler = menu_handler

    def set_on_move_callback(self, callback):
        self.on_move_callback = callback

    def create_interactive_marker(self, name, active = True):
        # retrieve pushable object marker
        marker = copy(self.object_marker)
        marker.header.frame_id = ""
        marker.color = self.object_color
        marker.color.a = 1.0

        # create interactive marker
        int_marker = InteractiveMarker()
        int_marker.name = name
        int_marker.description = name
        int_marker.header.frame_id = self.reference_frame
        int_marker.scale = 0.5
        int_marker.pose = self.object_pose
        int_marker.pose.position.z = marker.pose.position.z
        marker.pose = Pose(Point(0.0,0,0.0), Quaternion(0,0,0,1))

        # Create a controllable marker
        control = InteractiveMarkerControl( always_visible=True )
        control.interaction_mode = InteractiveMarkerControl.MOVE_PLANE
        control.orientation = Quaternion(0,1,0,1)
        control.markers.append( marker )
        int_marker.controls.append( control )

        # if active show interaction arrows
        if active:

            control = InteractiveMarkerControl( name="rotate_z" )
            control.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
            control.orientation=Quaternion(0,1,0,1)
            int_marker.controls.append(control)

            control = InteractiveMarkerControl( name="move_x" )
            control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
            control.orientation = Quaternion(0,0,1,1)
            int_marker.controls.append(control)

            control = InteractiveMarkerControl( name="move_y" )
            control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
            control.orientation = Quaternion(1,0,0,1)
            int_marker.controls.append(control)

            control = InteractiveMarkerControl( name="move_z" )
            control.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
            control.orientation = Quaternion(0,1,0,1)
            int_marker.controls.append(control)

        # register marker and move event callback
        self.server.insert(int_marker, self.on_move_cb)

    def reset_markers(self, active=True):
        self.create_interactive_marker( "sphere", active)
        self.server.applyChanges()

    def on_move_cb(self, feedback):
        if feedback.event_type == feedback.POSE_UPDATE:
            self.object_pose = feedback.pose
        if self.on_move_callback is not None:
            self.on_move_callback(feedback)

    def get_object_pose(self):
        return self.object_pose

if __name__=="__main__":
    rospy.init_node("interactive_push_markers_node")

    # prepare plan visualization with object marker
    marker = get_object_marker()

    # prepare interactive marker controls
    controls = InteractiveControls(marker)
    controls.reset_markers(True)

    # publish tf
    twist_pub = rospy.Publisher("/jog_server/delta_jog_cmds", TwistStamped, queue_size=1)
    twist = TwistStamped()

    rate = rospy.Rate(ODOM_UPDATE_RATE)  # Hz
    last_pose = controls.get_object_pose()
    step = 1.0 / ODOM_UPDATE_RATE
    vel_filter = 20
    #avg_x, avg_y, avg_z = 0.0, 0.0, 0.0
    while not rospy.is_shutdown():
        twist.header.stamp = rospy.Time.now()
        twist.header.frame_id = OBJECT_FRAME
        pose = controls.get_object_pose()
        twist.twist.linear.x = pose.position.x
        twist.twist.linear.y = pose.position.y
        twist.twist.linear.z = pose.position.z
        #avg_x = ((vel_filter - 1) * avg_x + (odom.pose.pose.position.x - last_pose.position.x) / step) / vel_filter
        #avg_y = ((vel_filter - 1) * avg_y + (odom.pose.pose.position.y - last_pose.position.y) / step) / vel_filter
        #avg_z = ((vel_filter - 1) * avg_z + (odom.pose.pose.position.z - last_pose.position.z) / step) / vel_filter
        #twist.twist.linear.x = avg_x
        #twist.twist.linear.y = avg_y
        #twist.twist.linear.z = avg_z
        twist_pub.publish(twist)
        #last_pose = odom.pose.pose
        rate.sleep()
