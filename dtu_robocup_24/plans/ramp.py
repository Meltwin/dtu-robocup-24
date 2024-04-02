from enum import Enum, auto
from raubase_ros.plan.conditions import (
    FlowTaskCondition,
    StartTaskCondition,
    FollowPreviousTask,
    StopTaskCondition,
    OnValue,
)
from raubase_ros.plan import BaseTask, close_to
import numpy as np

from raubase_ros.plan.data import Requirement


class TaskStep(Enum):
    TURN_DIR_RAMP = auto()
    GO_FOR_RAMP = auto()
    TURN_TO_STAIRS = auto()
    GO_TO_STAIRS = auto()
    TURN_AGAIN = auto()
    GO_THROUGH_STAIRS = auto()
    DONE = auto()


class RampTask(BaseTask):

    SPEED = 0.2

    def __init__(self) -> None:
        super().__init__()

        self.state = TaskStep.TURN_DIR_RAMP
        self.stop = False
        self.stop_cond = OnValue(lambda: self.stop)

    def start_condition(self) -> StartTaskCondition | FlowTaskCondition:
        return FollowPreviousTask()

    def stop_condition(self) -> StopTaskCondition | FlowTaskCondition:
        return self.stop_cond

    def requirements(self) -> Requirement:
        return Requirement.MOVE | Requirement.ODOMETRY | Requirement.MOVE_LINE

    def loop(self) -> None:

        match self.state:
            case TaskStep.TURN_DIR_RAMP:
                self.logger.info("Turning for the ramp ...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_h(0, -np.pi / 2)

                if close_to(self.data.odometry.heading, -np.pi / 2):
                    self.data.reset_distance()
                    self.state = TaskStep.GO_FOR_RAMP
                    
            case TaskStep.GO_FOR_RAMP:
                self.logger.info("Climbing the ramp ...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_w(RampTask.SPEED, 0)

                if self.data.distance >= 3.045:
                    self.data.reset_distance()
                    self.state = TaskStep.TURN_TO_STAIRS

            case TaskStep.TURN_TO_STAIRS:
                self.logger.info("Turn to the stairs...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_h(0, -np.pi / 2)

                if close_to(self.data.odometry.heading, -np.pi / 2):
                    self.data.reset_time()
                    self.state = TaskStep.GO_TO_STAIRS
                    
            case TaskStep.GO_TO_STAIRS:
                self.logger.info("Going to the stairs...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_w(RampTask.SPEED, 0)

                if self.data.distance >= 0.6:
                    self.data.reset_distance()
                    self.state = TaskStep.TURN_AGAIN
                    
            case TaskStep.TURN_AGAIN:
                self.logger.info("Turn again for stairs...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_h(0, -np.pi / 2)

                if close_to(self.data.odometry.heading, -np.pi / 2):
                    self.data.reset_time()
                    self.state = TaskStep.GO_THROUGH_STAIRS
                    
            case TaskStep.GO_THROUGH_STAIRS:
                self.logger.info("Going through the stairs ...",
                throttle_duration_sec=0.5,)
                self.control.set_vel_w(RampTask.SPEED, 0)

                if self.data.distance >= 2.965:
                    self.data.reset_distance()
                    self.state = TaskStep.DONE

            case TaskStep.DONE:
                self.control.set_vel_w(0, 0)
                self.stop = True
