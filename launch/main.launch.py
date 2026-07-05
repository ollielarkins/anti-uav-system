from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('anti_uav_system')

    swarm_size = LaunchConfiguration('swarm_size', default='8')

    return LaunchDescription([
        DeclareLaunchArgument('swarm_size', default_value='8',
                              description='Number of simulated UAVs'),

        # rosbridge WebSocket server (HUD connects here)
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge',
            parameters=[{'port': 9090}],
        ),

        # Camera feed HTTP server (HUD MJPEG stream)
        Node(
            package='web_video_server',
            executable='web_video_server',
            name='video_server',
            parameters=[{'port': 8080}],
        ),

        # Detection node (YOLOv8) — uncomment when built
        # Node(
        #     package='anti_uav_system',
        #     executable='yolo_node',
        #     name='yolo_node',
        #     parameters=[PathJoinSubstitution([pkg, 'config', 'sim.yaml'])],
        # ),

        # Tracker node — uncomment when built
        # Node(
        #     package='anti_uav_system',
        #     executable='tracker_node',
        #     name='tracker_node',
        #     parameters=[PathJoinSubstitution([pkg, 'config', 'tracker.yaml'])],
        # ),

        # Ballistics node — uncomment when built
        # Node(
        #     package='anti_uav_system',
        #     executable='ballistics_node',
        #     name='ballistics_node',
        #     parameters=[PathJoinSubstitution([pkg, 'config', 'ballistics.yaml'])],
        # ),
    ])
