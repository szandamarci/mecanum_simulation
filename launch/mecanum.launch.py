import os
import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    package_name = 'mecanum_custom'
    bringup_dir = get_package_share_directory('nav2_bringup')
    local_dir = get_package_share_directory(package_name)
    world_file = os.path.join(local_dir, 'worlds/plain.world')
    rviz_dir = os.path.join(local_dir, 'rviz')
    xacro_file = os.path.join(local_dir, 'urdf/mecanum.xacro')
    description_raw = xacro.process_file(xacro_file).toxml()
    joy_config = launch.substitutions.LaunchConfiguration('joy_config')
    joy_dev = launch.substitutions.LaunchConfiguration('joy_dev')
    publish_stamped_twist = launch.substitutions.LaunchConfiguration('publish_stamped_twist')
    config_filepath = launch.substitutions.LaunchConfiguration('config_filepath')

    # urdf_file = os.path.join(local_dir, 'urdf/mecanum.urdf')
    # with open(urdf_file, 'r') as infp:
    #     description_raw = infp.read()

    map_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    slam = LaunchConfiguration('slam')
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')

    spawn_entity = Node(package= 'gazebo_ros',
                        executable='spawn_entity.py',
                        arguments=[
                            '-topic', 'robot_description',
                            '-entity', 'my_bot'],
                        output='screen')

    robot_state_publisher = Node(package= 'robot_state_publisher',
                        executable='robot_state_publisher',
                        parameters=[
                            {'robot_description' : description_raw,
                             'use_sim_time' : use_sim_time}],
                        output='screen')
    
    joint_state_publisher = Node(package= 'joint_state_publisher',
                        executable='joint_state_publisher',
                        parameters=[
                            {'robot_description' : description_raw,
                             'use_sim_time' : use_sim_time}],
                        output='screen')
    

    rviz = Node(package= 'rviz2',
                namespace='',
                executable='rviz2',
                name='rviz2',
                arguments=[
                    '-d', [os.path.join(rviz_dir, 'fourwheel.rviz')]],
                output='screen')
    
    start_nav_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(local_dir, 'launch/nav2.launch.py')),
        launch_arguments={
            'map' : map_file,
            'use_sim_time' : 'True',
            'params_file' : params_file,
            'slam' : slam 
        }.items())
    
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map', 
        default_value=os.path.join(
            bringup_dir, 'maps', 'turtlebot3_world.yaml'),
        description='Path to map file'
        )
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file', 
        default_value=os.path.join(
            local_dir, 'params', 'nav2_params_four.yaml'),
        description='Path to nav2 parameters file'
        )
    
    declare_slam_cmd = DeclareLaunchArgument(
        'slam', 
        default_value='True',
        description='Run slam or not'
        )
    
    declare_gui_cmd = DeclareLaunchArgument('gui', default_value='true',
                              description='Run GUI')
    
    declare_gzserver_cmd = DeclareLaunchArgument('server', default_value='true',
                              description='Run gzserver')
    

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gzserver.launch.py')),
            condition=IfCondition(LaunchConfiguration('server')),
            launch_arguments={
                'world' : world_file,
                'use_sim_time' : 'True'
            }.items()
    )

    gui= IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gzclient.launch.py')),
            condition=IfCondition(LaunchConfiguration('gui')),
            launch_arguments={
                'world' : world_file,
                'use_sim_time' : 'True'
            }.items()
    )

    joy = Node(package ='joy',
               executable='joy_node',
               name='joy_node',
               parameters=[
                   {
                       'device_id': joy_dev,
                       'deadzone': 0.3,
                       'autorepeat_rate': 20.0,
                   }
               ]
    )

    teleop = Node(package= 'teleop_twist_joy',
                namespace='',
                executable='teleop_node',
                name='teleop_twist_joy_node',
                parameters=[config_filepath, {'publish_stamped_twist': publish_stamped_twist}],
                remappings={('/cmd_vel', launch.substitutions.LaunchConfiguration('joy_vel'))}
                )

    declare_joy_vel = DeclareLaunchArgument('joy_vel', default_value='cmd_vel')
    declare_joy_config = DeclareLaunchArgument('joy_config', default_value='xbox')
    declare_joy_dev = DeclareLaunchArgument('joy_dev', default_value='0')
    declare_publish_stamped_twist = DeclareLaunchArgument('publish_stamped_twist', default_value='false')
    declare_config_filepath = DeclareLaunchArgument('config_filepath', default_value=[
        launch.substitutions.TextSubstitution(text=os.path.join(
            get_package_share_directory('teleop_twist_joy'), 'config', '')),
            joy_config, launch.substitutions.TextSubstitution(text='.config.yaml')])
    
    return LaunchDescription([
        
        declare_gui_cmd,
        declare_gzserver_cmd,
        declare_map_yaml_cmd,
        declare_params_file_cmd,
        declare_slam_cmd,
        declare_joy_vel,
        declare_joy_config,
        declare_joy_dev,
        declare_publish_stamped_twist,
        declare_config_filepath,
        gzserver,
        gui,
        spawn_entity,
        robot_state_publisher,
        joint_state_publisher, 
        rviz,
        start_nav_cmd,
        joy, 
        teleop

    ])


