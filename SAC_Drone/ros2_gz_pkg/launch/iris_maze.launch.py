# # Copyright 2023 ArduPilot.org.
# #
# # This program is free software: you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with this program. If not, see <https://www.gnu.org/licenses/>.

# # Adapted from https://github.com/gazebosim/ros_gz_project_template
# #
# # Copyright 2019 Open Source Robotics Foundation, Inc.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# # """Launch an iris quadcopter in Gazebo and Rviz."""
# # from pathlib import Path

# # from ament_index_python.packages import get_package_share_directory

# # from launch import LaunchDescription
# # from launch.actions import DeclareLaunchArgument
# # from launch.actions import IncludeLaunchDescription
# # from launch.conditions import IfCondition
# # from launch.launch_description_sources import PythonLaunchDescriptionSource
# # from launch.substitutions import LaunchConfiguration
# # from launch.substitutions import PathJoinSubstitution

# # from launch_ros.actions import Node
# # from launch_ros.substitutions import FindPackageShare


# # def generate_launch_description():
# #     """Generate a launch description for a iris quadcopter."""
# #     pkg_project_bringup = get_package_share_directory("py_launch_example")
# #     pkg_project_gazebo = get_package_share_directory("ardupilot_gz_gazebo")
# #     pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

# #     # Iris.
# #     iris = IncludeLaunchDescription(
# #         PythonLaunchDescriptionSource(
# #             [
# #                 PathJoinSubstitution(
# #                     [
# #                         FindPackageShare("py_launch_example"),
# #                         "launch",
# #                         "robots",
# #                         "iris_lidar.launch.py",
# #                     ]
# #                 ),
# #             ]
# #         )
# #     )

# #     # Gazebo.
# #     gz_sim_server = IncludeLaunchDescription(
# #         PythonLaunchDescriptionSource(
# #             f'{Path(pkg_ros_gz_sim) / "launch" / "gz_sim.launch.py"}'
# #         ),
# #         launch_arguments={
# #             "gz_args": "-v4 -s -r "
# #             + "/home/shibin/ros2_ws/src/py_launch_example/worlds/iris_maze.sdf"
# #         }.items(),
# #     )

# #     gz_sim_gui = IncludeLaunchDescription(
# #         PythonLaunchDescriptionSource(
# #             f'{Path(pkg_ros_gz_sim) / "launch" / "gz_sim.launch.py"}'
# #         ),
# #         launch_arguments={"gz_args": "-v4 -g"}.items(),
# #     )

# #     # RViz.
# #     rviz = Node(
# #         package="rviz2",
# #         executable="rviz2",
# #         arguments=[
# #             "-d",
# #             f'{Path(pkg_project_bringup) / "rviz" / "iris_with_lidar.rviz"}',
# #         ],
# #         condition=IfCondition(LaunchConfiguration("rviz")),
# #     )

# #     return LaunchDescription(
# #         [
# #             DeclareLaunchArgument(
# #                 "rviz", default_value="true", description="Open RViz."
# #             ),
# #             gz_sim_server,
# #             gz_sim_gui,
# #             iris,
# #             rviz,
# #         ]
# #     )



import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """Generate a launch description for an iris quadcopter."""
    pkg_py_launch_example = get_package_share_directory("py_launch_example")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Ensure `SDF_PATH` is populated as `sdformat_urdf` uses this rather
    # than `GZ_SIM_RESOURCE_PATH` to locate resources.
    if "GZ_SIM_RESOURCE_PATH" in os.environ:
        gz_sim_resource_path = os.environ["GZ_SIM_RESOURCE_PATH"]

        if "SDF_PATH" in os.environ:
            sdf_path = os.environ["SDF_PATH"]
            os.environ["SDF_PATH"] = sdf_path + ":" + gz_sim_resource_path
        else:
            os.environ["SDF_PATH"] = gz_sim_resource_path

    # Load SDF file.
    sdf_file = os.path.join(
        pkg_py_launch_example, "models", "iris_with_lidar", "model.sdf"
    )
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    # Gazebo simulation.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
           'gz_args': '-r ' + os.path.join(pkg_py_launch_example, 'worlds', 'iris_maze.sdf')
        }.items(),
    )

    # RViz.
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(pkg_py_launch_example, "rviz", "iris_with_lidar.rviz"),
        ],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    # Robot state publisher.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[
            {"robot_description": robot_desc},
            {"frame_prefix": ""},
        ],
    )

    # Bridge.
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    pkg_py_launch_example, "config", "iris_lidar_bridge.yaml"
                ),
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        output="screen",
    )

    # Relay - use instead of transform when Gazebo is only publishing odom -> base_link
    topic_tools_tf = Node(
        package="topic_tools",
        executable="relay",
        arguments=[
            "/gz/tf",
            "/tf",
        ],
        output="screen",
        respawn=False,
        condition=IfCondition(LaunchConfiguration("use_gz_tf")),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "rviz", default_value="true", description="Open RViz."
            ),
            DeclareLaunchArgument(
                "use_gz_tf", default_value="true", description="Use Gazebo TF."
            ),
            robot_state_publisher,
            bridge,
            RegisterEventHandler(
                OnProcessStart(
                    target_action=bridge,
                    on_start=[topic_tools_tf]
                )
            ),
            rviz,
            gz_sim,
        ]
    )

