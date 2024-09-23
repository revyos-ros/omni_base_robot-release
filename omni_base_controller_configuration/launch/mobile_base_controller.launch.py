# Copyright (c) 2024 PAL Robotics S.L. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
import os

from ament_index_python.packages import get_package_share_directory
from controller_manager.launch_utils import generate_load_controller_launch_description
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import PythonExpression
from launch_ros.actions import Node
from launch_pal.robot_arguments import CommonArgs
from launch_pal.arg_utils import LaunchArgumentsBase


@dataclass(frozen=True)
class LaunchArguments(LaunchArgumentsBase):
    use_sim_time: DeclareLaunchArgument = CommonArgs.use_sim_time
    is_public_sim: DeclareLaunchArgument = CommonArgs.is_public_sim


def generate_launch_description():

    # Create the launch description and populate
    ld = LaunchDescription()
    launch_arguments = LaunchArguments()

    launch_arguments.add_to_launch_description(ld)

    declare_actions(ld, launch_arguments)

    return ld


def declare_actions(
    launch_description: LaunchDescription, launch_args: LaunchArguments
):
    pkg_share_folder = get_package_share_directory('omni_base_controller_configuration')

    # Temporary Fix when using rolling version of ros2 control
    twist_relay = Node(
        package='topic_tools',
        executable='relay_field',
        name='twist_relay',
        arguments=['/mobile_base_controller/cmd_vel', '/mobile_base_controller/cmd_vel_unstamped',
                   'geometry_msgs/Twist', '{linear: m.twist.linear, angular: m.twist.angular}'],
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration('is_public_sim'),
                    "' != 'True' and '",
                    LaunchConfiguration('use_sim_time'),
                    "' == 'True'"
                ]
            )
        ))

    launch_description.add_action(twist_relay)

    # Base controller
    base_controller = GroupAction(
        [
            generate_load_controller_launch_description(
                controller_name='mobile_base_controller',
                controller_params_file=os.path.join(
                    pkg_share_folder, 'config', 'mobile_base_controller.yaml')
            )
        ],
        condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
    )
    launch_description.add_action(base_controller)

    return
