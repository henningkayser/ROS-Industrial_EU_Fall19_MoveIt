#!/bin/bash

WS=$HOME/ros

mkdir -p $WS/src
wstool init $WS/src https://raw.githubusercontent.com/henningkayser/panda_robot_env/master/panda_robot_env.rosinstall

cd $WS
catkin init
catkin config --extend /opt/ros/melodic
catkin build

echo 'source $HOME/ros/devel/setup.bash' >> $HOME/.bashrc
