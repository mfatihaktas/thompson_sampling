import pytest
import simpy

from typing import Callable

from src.sys import (
    scheduler as scheduler_module,
    server as server_module,
    sink as sink_module,
    source as source_module,
)
from src.agent import (
    agent as agent_module,
    ts as ts_module,
)
from src.prob import random_variable
from src.sim import sim as sim_module

from src.utils.debug import *
from src.utils.plot import *


@pytest.fixture(scope="module")
def env() -> simpy.Environment:
    return simpy.Environment()


@pytest.fixture(scope="module")
def num_servers() -> int:
    return 2


@pytest.fixture(scope="module")
def num_servers() -> int:
    return 2


@pytest.fixture(scope="module")
def inter_task_gen_time_rv() -> random_variable.RandomVariable:
    return random_variable.Exponential(mu=1)


@pytest.fixture(scope="module")
def task_service_time_rv() -> random_variable.RandomVariable:
    return random_variable.DiscreteUniform(min_value=1, max_value=1)


def sim(
    env: simpy.Environment,
    num_servers: int,
    inter_task_gen_time_rv: random_variable.RandomVariable,
    task_service_time_rv: random_variable.RandomVariable,
    num_tasks_to_recv: int,
    sching_agent_given_server_list: Callable[[list[server_module.Server]], agent_module.SchingAgent],
) -> sim_module.SimResult:
    return sim_module.sim(
        env=env,
        num_servers=num_servers,
        inter_task_gen_time_rv=inter_task_gen_time_rv,
        task_service_time_rv=task_service_time_rv,
        num_tasks_to_recv=num_tasks_to_recv,
        sching_agent_given_server_list=sching_agent_given_server_list,
    )


def test_ThompsonSampling_slidingWin(
    env: simpy.Environment,
    num_servers: int,
    inter_task_gen_time_rv: random_variable.RandomVariable,
    task_service_time_rv: random_variable.RandomVariable,
):
    def ts_sliding_win(server_list: list[server_module.Server]):
        return ts_module.ThompsonSampling_slidingWin(
            node_id_list=[s._id for s in server_list],
            win_len=100,
        )

    sim_result = sim(
        env=env,
        num_servers=num_servers,
        inter_task_gen_time_rv=inter_task_gen_time_rv,
        task_service_time_rv=task_service_time_rv,
        num_tasks_to_recv=100,
        sching_agent_given_server_list=ts_sliding_win,
    )
    log(INFO, "", sim_result=sim_result)


def test_ThompsonSampling_slidingWin_vs_slidingWinForEachNode(
    env: simpy.Environment,
    num_servers: int,
    inter_task_gen_time_rv: random_variable.RandomVariable,
    task_service_time_rv: random_variable.RandomVariable,
):
    num_tasks_to_recv = 100
    def sim_(win_len: int):
        def ts_sliding_win(server_list: list[server_module.Server]):
            return ts_module.ThompsonSampling_slidingWin(
                node_id_list=[s._id for s in server_list],
                win_len=100,
            )

        def ts_sliding_win_for_each_node(server_list: list[server_module.Server]):
            return ts_module.ThompsonSampling_slidingWinForEachNode(
                node_id_list=[s._id for s in server_list],
                win_len=100,
            )

        sim_result_for_slidingWin = sim(
            env=env,
            num_servers=num_servers,
            inter_task_gen_time_rv=inter_task_gen_time_rv,
            task_service_time_rv=task_service_time_rv,
            num_tasks_to_recv=num_tasks_to_recv,
            sching_agent_given_server_list=ts_sliding_win,
        )

        sim_result_for_slidingWinForEachNode = sim(
            env=env,
            num_servers=num_servers,
            inter_task_gen_time_rv=inter_task_gen_time_rv,
            task_service_time_rv=task_service_time_rv,
            num_tasks_to_recv=num_tasks_to_recv,
            sching_agent_given_server_list=ts_sliding_win,
        )

        return sim_result_for_slidingWin, sim_result_for_slidingWinForEachNode

    # Run the sim
    win_len_list = []
    ET_slidingWin_list, ET_slidingWinForEachNode_list = [], []
    for win_len in [10, 100, 1000]:
        logger.info(f">> win_len= {win_len}")
        win_len_list.append(win_len)

        sim_result_for_slidingWin, sim_result_for_slidingWinForEachNode = sim_(win_len=win_len)
        logger.info(
            "\n"
            f"sim_result_for_slidingWin= {sim_result_for_slidingWin} \n"
            f"sim_result_for_slidingWinForEachNode= {sim_result_for_slidingWinForEachNode}"
        )

    # Save the plot
    fontsize = 14
    plot.legend(fontsize=fontsize)
    plot.ylabel(r"$E[T]$", fontsize=fontsize)
    plot.xlabel(r"$w$", fontsize=fontsize)
    plot.title(sim_config.get_plot_title())
    plot.gcf().set_size_inches(6, 4)
    plot.savefig("plot_ThompsonSampling_slidingWin_vs_slidingWinForEachNode_ET_vs_w.png", bbox_inches="tight")
    plot.gcf().clear()

    log(INFO, "Done")
