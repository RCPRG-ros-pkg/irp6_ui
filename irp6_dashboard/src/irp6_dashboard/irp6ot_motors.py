# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

#
# Ported from pr2_motors: Vincent Rabaud, Aldebaran Robotics, 2014
#

from python_qt_binding.QtCore import QT_VERSION_STR
if (QT_VERSION_STR >= '5'):
	from python_qt_binding.QtWidgets import QMessageBox
else:
	from python_qt_binding.QtGui import QMessageBox

import actionlib
import rospy
from rqt_robot_dashboard.widgets import MenuDashWidget
import std_srvs.srv

from std_msgs.msg import *
from irpos import *
from .irp6_motors import Irp6MotorStatus, Irp6Motors

class Irp6otMotors(Irp6Motors):
    """
    Dashboard widget to display motor state and allow interaction.
    """
    def __init__(self, context):
        """
        :param context: the plugin context
        :type context: qt_gui.plugin.Plugin
        :param reset_callback: calback for the "reset" action
        :type reset_callback: function
        :param halt_callback: calback for the "reset" action
        :type halt_callback: function
        """

        super(Irp6otMotors, self).__init__('Irp6otMotors')
        
        
        
        self.move_to_synchro_pos_action = self.add_action('Irp6ot move to synchro pos', self.move_to_synchro_pos)
        self.move_to_front_pos_action = self.add_action('Irp6ot move to front pos', self.move_to_front_pos)
        self.synchronise_action = self.add_action('Irp6ot Synchronise', self.synchronise)
                
        self.change_motors_widget_state()
        timerThread = threading.Thread(target=self.monitor_robot_activity)
        timerThread.daemon = True
        timerThread.start()
        self.emergency_stop_pub = rospy.Publisher('/irp6ot_supervisor/emergency_stop_in', std_msgs.msg.Bool, queue_size=0)
        self.synchro_pub = rospy.Publisher('/irp6ot_supervisor/do_synchro_in', std_msgs.msg.Bool, queue_size=0)
      


    def irp6otm_done_callback(self,state, result):
        self.conmanSwitch([], ['Irp6otmSplineTrajectoryGeneratorMotor','Irp6otmSplineTrajectoryGeneratorJoint','Irp6otmPoseInt','Irp6otmForceControlLaw','Irp6otmForceTransformation'], True)
        self.status.motion_in_progress = False
        self.change_motors_widget_state()


    def irp6ottfg_done_callback(self,state, result):
        self.conmanSwitch([], ['Irp6ottfgSplineTrajectoryGeneratorMotor'], True)
        self.status.motion_in_progress = False
        self.change_motors_widget_state()


    def init_conman(self):
        rospy.wait_for_service('/irp6ot_manager/switch_controller')
        self.conmanSwitch = rospy.ServiceProxy('/irp6ot_manager/switch_controller', SwitchController)


    def move_to_synchro_pos(self):
        self.init_conman()
        self.conmanSwitch([], ['Irp6ottfgSplineTrajectoryGeneratorMotor','Irp6otmSplineTrajectoryGeneratorMotor','Irp6otmSplineTrajectoryGeneratorJoint','Irp6otmPoseInt','Irp6otmForceControlLaw','Irp6otmForceTransformation'], True)
  
        self.conmanSwitch(['Irp6otmSplineTrajectoryGeneratorMotor'], [], True)
    
        self.client_m = actionlib.SimpleActionClient('/irp6ot_arm/spline_trajectory_action_motor', FollowJointTrajectoryAction)
        self.client_m.wait_for_server()

        goal_m = FollowJointTrajectoryGoal()
        goal_m.trajectory.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7']
        goal_m.trajectory.points.append(JointTrajectoryPoint([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [], [], rospy.Duration(10.0)))
        goal_m.trajectory.header.stamp = rospy.get_rostime() + rospy.Duration(0.2)

        self.client_m.send_goal(goal_m, self.irp6otm_done_callback)
        
        self.client_tfg = actionlib.SimpleActionClient('/irp6ot_tfg/spline_trajectory_action_motor', FollowJointTrajectoryAction)
        self.client_tfg.wait_for_server()
        
        self.conmanSwitch(['Irp6ottfgSplineTrajectoryGeneratorMotor'], [], True)

        goal_tfg = FollowJointTrajectoryGoal()
        goal_tfg.trajectory.joint_names = ['joint1']
        goal_tfg.trajectory.points.append(JointTrajectoryPoint([0.0], [0.0], [], [], rospy.Duration(10.0)))
        goal_tfg.trajectory.header.stamp = rospy.get_rostime() + rospy.Duration(0.2)

        self.client_tfg.send_goal(goal_tfg, self.irp6ottfg_done_callback)
  
        self.status.motion_in_progress = True
        self.change_motors_widget_state()


    def move_to_front_pos(self):
        self.init_conman()
        self.conmanSwitch([], ['Irp6otmSplineTrajectoryGeneratorMotor','Irp6otmSplineTrajectoryGeneratorJoint','Irp6otmPoseInt','Irp6otmForceControlLaw','Irp6otmForceTransformation'], True)
  
        self.conmanSwitch(['Irp6otmSplineTrajectoryGeneratorJoint'], [], True)
    
        self.client = actionlib.SimpleActionClient('/irp6ot_arm/spline_trajectory_action_joint', FollowJointTrajectoryAction)
        self.client.wait_for_server()

        goal = FollowJointTrajectoryGoal()
        goal.trajectory.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7']
        goal.trajectory.points.append(JointTrajectoryPoint([0.0, 0.0, -1.57, 0.0, 1.5, 1.57, -1.57], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [], [], rospy.Duration(10.0)))
        goal.trajectory.header.stamp = rospy.get_rostime() + rospy.Duration(0.2)
        
        self.client.send_goal(goal, self.irp6otm_done_callback)
        self.status.motion_in_progress = True
        self.change_motors_widget_state()


