import numpy
import simpy

from src.agent import (
    optimal as optimal_module,
    random as random_module,
    ts as ts_module,
)
from src.prob import random_variable
from src.sim import sim as sim_module
from src.sys import server as server_module

from src.utils.debug import *
from src.utils.plot import *


def optimal_vs_ts(
    env: simpy.Environment,
    num_servers: int,
    task_service_time_rv: random_variable.RandomVariable,
    num_tasks_to_recv: int = 1000,
    win_len: int = 100,
    num_sim_runs: int = 3,
):
    log(INFO, "Started",
        num_servers=num_servers,
        task_service_time_rv=task_service_time_rv,
        num_tasks_to_recv=num_tasks_to_recv,
        num_sim_runs=num_sim_runs,
    )

    # Callbacks that return the sching agents
    def assign_w_random(server_list: list[server_module.Server]):
        return random_module.AssignToRandom(node_list=server_list)

    def assign_w_ts_sliding_win(server_list: list[server_module.Server]):
        return ts_module.AssignWithThompsonSampling_slidingWin(
            node_list=server_list,
            win_len=win_len,
        )

    def assign_w_ts_sliding_win_for_each_node(server_list: list[server_module.Server]):
        return ts_module.AssignWithThompsonSampling_slidingWinForEachNode(
            node_list=server_list,
            win_len=win_len,
        )

    def assign_w_ts_reset_win_on_rare_event(server_list: list[server_module.Server]):
        return ts_module.AssignWithThompsonSampling_resetWinOnRareEvent(
            node_list=server_list,
            win_len=win_len,
            threshold_prob_rare=0.9,
        )

    def assign_to_least_work_left(server_list: list[server_module.Server]):
        return optimal_module.AssignToLeastWorkLeft(node_list=server_list)

    def assign_to_noisy_least_work_left(server_list: list[server_module.Server]):
        return optimal_module.AssignToNoisyLeastWorkLeft(
            node_list=server_list,
            noise_rv=random_variable.CustomDiscrete(
                value_list=[0.5, 0.75, 1, 1.25, 1.5],
                prob_weight_list=[1, 1, 1, 1, 1],
            )
        )

    def assign_to_very_noisy_least_work_left(server_list: list[server_module.Server]):
        return optimal_module.AssignToNoisyLeastWorkLeft(
            node_list=server_list,
            noise_rv=random_variable.CustomDiscrete(
                value_list=[0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
                prob_weight_list=[1, 1, 1, 1, 1, 1, 1, 1],
            )
        )

    def assign_to_fewest_tasks_left(server_list: list[server_module.Server]):
        return optimal_module.AssignToFewestTasksLeft(node_list=server_list)

    def sim_(arrival_rate: float):
        inter_task_gen_time_rv = random_variable.Exponential(mu=arrival_rate)

        def sim_result(sching_agent_given_server_list):
            return sim_module.sim_w_joblib(
                env=env,
                num_servers=num_servers,
                inter_task_gen_time_rv=inter_task_gen_time_rv,
                task_service_time_rv=task_service_time_rv,
                num_tasks_to_recv=num_tasks_to_recv,
                sching_agent_given_server_list=sching_agent_given_server_list,
                num_sim_runs=num_sim_runs,
            )

        sim_result_for_assign_to_random = sim_result(sching_agent_given_server_list=assign_w_random)
        sim_result_for_ts_sliding_win = None # sim_result(sching_agent_given_server_list=assign_w_ts_sliding_win)
        sim_result_for_ts_sliding_win_for_each_node = None # sim_result(sching_agent_given_server_list=assign_w_ts_sliding_win_for_each_node)
        sim_result_for_ts_reset_win_on_rare_event = sim_result(sching_agent_given_server_list=assign_w_ts_reset_win_on_rare_event)
        sim_result_for_assign_to_least_work_left = None # sim_result(sching_agent_given_server_list=assign_to_least_work_left)
        sim_result_for_assign_to_noisy_least_work_left = None # sim_result(sching_agent_given_server_list=assign_to_noisy_least_work_left)
        sim_result_for_assign_to_very_noisy_least_work_left = None # sim_result(sching_agent_given_server_list=assign_to_very_noisy_least_work_left)
        sim_result_for_assign_to_fewest_tasks_left = sim_result(sching_agent_given_server_list=assign_to_fewest_tasks_left)

        return (
            sim_result_for_assign_to_random,
            sim_result_for_ts_sliding_win,
            sim_result_for_ts_sliding_win_for_each_node,
            sim_result_for_ts_reset_win_on_rare_event,
            sim_result_for_assign_to_least_work_left,
            sim_result_for_assign_to_noisy_least_work_left,
            sim_result_for_assign_to_very_noisy_least_work_left,
            sim_result_for_assign_to_fewest_tasks_left
        )

    # Run the sim
    # arrival_rate_list = list(numpy.linspace(0.1, num_servers, num=4, endpoint=False))
    arrival_rate_list = [0.1*num_servers, 0.5*num_servers, 0.8*num_servers]
    # arrival_rate_list = [0.5*num_servers, 0.8*num_servers]
    # arrival_rate_list = [0.1*num_servers, 0.25*num_servers, 0.5*num_servers, 0.65*num_servers, 0.8*num_servers]
    ET_random_list, std_T_random_list = [], []
    ET_ts_sliding_win_list, std_T_ts_sliding_win_list = [], []
    ET_ts_sliding_win_for_each_node_list, std_T_ts_sliding_win_for_each_node_list = [], []
    ET_ts_reset_win_on_rare_event_list, std_T_ts_reset_win_on_rare_event_list = [], []
    ET_to_least_work_left_list, ET_to_noisy_least_work_left_list, ET_to_very_noisy_least_work_left_list, ET_to_fewest_tasks_left_list = [], [], [], []
    std_T_to_least_work_left_list, std_T_to_noisy_least_work_left_list, std_T_to_very_noisy_least_work_left_list, std_T_to_fewest_tasks_left_list = [], [], [], []
    for arrival_rate in arrival_rate_list:
        log(INFO, f">> arrival_rate= {arrival_rate}")

        (
            sim_result_for_assign_to_random,
            sim_result_for_ts_sliding_win,
            sim_result_for_ts_sliding_win_for_each_node,
            sim_result_for_ts_reset_win_on_rare_event,
            sim_result_for_assign_to_least_work_left,
            sim_result_for_assign_to_noisy_least_work_left,
            sim_result_for_assign_to_very_noisy_least_work_left,
            sim_result_for_assign_to_fewest_tasks_left
        ) = sim_(arrival_rate=arrival_rate)
        log(INFO, "",
            sim_result_for_assign_to_random=sim_result_for_assign_to_random,
            sim_result_for_ts_sliding_win=sim_result_for_ts_sliding_win,
            sim_result_for_ts_sliding_win_for_each_node=sim_result_for_ts_sliding_win_for_each_node,
            sim_result_for_ts_reset_win_on_rare_event=sim_result_for_ts_reset_win_on_rare_event,
            sim_result_for_assign_to_least_work_left=sim_result_for_assign_to_least_work_left,
            sim_result_for_assign_to_noisy_least_work_left=sim_result_for_assign_to_noisy_least_work_left,
            sim_result_for_assign_to_very_noisy_least_work_left=sim_result_for_assign_to_very_noisy_least_work_left,
            sim_result_for_assign_to_fewest_tasks_left=sim_result_for_assign_to_fewest_tasks_left,
        )

        if sim_result_for_assign_to_random:
            ET_random_list.append(sim_result_for_assign_to_random.ET)
            std_T_random_list.append(sim_result_for_assign_to_random.std_T)

        if sim_result_for_ts_sliding_win:
            ET_ts_sliding_win_list.append(sim_result_for_ts_sliding_win.ET)
            std_T_ts_sliding_win_list.append(sim_result_for_ts_sliding_win.std_T)

        if sim_result_for_ts_sliding_win_for_each_node:
            ET_ts_sliding_win_for_each_node_list.append(sim_result_for_ts_sliding_win_for_each_node.ET)
            std_T_ts_sliding_win_for_each_node_list.append(sim_result_for_ts_sliding_win_for_each_node.std_T)

        if sim_result_for_ts_reset_win_on_rare_event:
            ET_ts_reset_win_on_rare_event_list.append(sim_result_for_ts_reset_win_on_rare_event.ET)
            std_T_ts_reset_win_on_rare_event_list.append(sim_result_for_ts_reset_win_on_rare_event.std_T)

        if sim_result_for_assign_to_least_work_left:
            ET_to_least_work_left_list.append(sim_result_for_assign_to_least_work_left.ET)
            std_T_to_least_work_left_list.append(sim_result_for_assign_to_least_work_left.std_T)

        if sim_result_for_assign_to_noisy_least_work_left:
            ET_to_noisy_least_work_left_list.append(sim_result_for_assign_to_noisy_least_work_left.ET)
            std_T_to_noisy_least_work_left_list.append(sim_result_for_assign_to_noisy_least_work_left.std_T)

        if sim_result_for_assign_to_very_noisy_least_work_left:
            ET_to_very_noisy_least_work_left_list.append(sim_result_for_assign_to_very_noisy_least_work_left.ET)
            std_T_to_very_noisy_least_work_left_list.append(sim_result_for_assign_to_very_noisy_least_work_left.std_T)

        if sim_result_for_assign_to_fewest_tasks_left:
            ET_to_fewest_tasks_left_list.append(sim_result_for_assign_to_fewest_tasks_left.ET)
            std_T_to_fewest_tasks_left_list.append(sim_result_for_assign_to_fewest_tasks_left.std_T)

    '''
    plot.errorbar(arrival_rate_list, ET_random_list, yerr=std_T_random_list, color=next(dark_color_cycle), label="Random", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.errorbar(arrival_rate_list, ET_ts_sliding_win_list, yerr=std_T_ts_sliding_win_list, color=next(dark_color_cycle), label="TS-SlidingWin", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.errorbar(arrival_rate_list, ET_ts_sliding_win_for_each_node_list, yerr=std_T_ts_sliding_win_for_each_node_list, color=next(dark_color_cycle), label="TS-SlidingWinForEachNode", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.errorbar(arrival_rate_list, ET_ts_reset_win_on_rare_event_list, yerr=std_T_ts_reset_win_on_rare_event_list, color=next(dark_color_cycle), label="TS-ResetWinOnRareEvent", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.errorbar(arrival_rate_list, ET_to_least_work_left_list, yerr=std_T_to_least_work_left_list, color=next(dark_color_cycle), label="AssignToLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.errorbar(arrival_rate_list, ET_to_noisy_least_work_left_list, yerr=std_T_to_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.errorbar(arrival_rate_list, ET_to_very_noisy_least_work_left_list, yerr=std_T_to_very_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToVeryNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.errorbar(arrival_rate_list, ET_to_fewest_tasks_left_list, yerr=std_T_to_fewest_tasks_left_list, color=next(dark_color_cycle), label="AssignToFewestTasksLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    '''

    fig, axs = plot.subplots(1, 2)
    fontsize = 14

    # E[T] vs lambda
    ax = axs[0]
    plot.sca(ax)

    plot.plot(arrival_rate_list, ET_random_list, color=next(dark_color_cycle), label="Random", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, ET_ts_sliding_win_list, color=next(dark_color_cycle), label="TS-SlidingWin", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, ET_ts_sliding_win_for_each_node_list, color=next(dark_color_cycle), label="TS-SlidingWinForEachNode", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.plot(arrival_rate_list, ET_ts_reset_win_on_rare_event_list, color=next(dark_color_cycle), label="TS-ResetWinOnRareEvent", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, ET_to_least_work_left_list, color=next(dark_color_cycle), label="AssignToLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, ET_to_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, ET_to_very_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToVeryNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.plot(arrival_rate_list, ET_to_fewest_tasks_left_list, color=next(dark_color_cycle), label="AssignToFewestTasksLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)

    plot.legend(fontsize=fontsize)
    plot.ylabel(r"$E[T]$", fontsize=fontsize)
    plot.yscale("log")
    plot.xlabel(r"$\lambda$", fontsize=fontsize)

    # Stdev[T] vs lambda
    ax = axs[1]
    plot.sca(ax)

    plot.plot(arrival_rate_list, std_T_random_list, color=next(dark_color_cycle), label="Random", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, std_T_ts_sliding_win_list, color=next(dark_color_cycle), label="TS-SlidingWin", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, std_T_ts_sliding_win_for_each_node_list, color=next(dark_color_cycle), label="TS-SlidingWinForEachNode", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.plot(arrival_rate_list, std_T_ts_reset_win_on_rare_event_list, color=next(dark_color_cycle), label="TS-ResetWinOnRareEvent", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, std_T_to_least_work_left_list, color=next(dark_color_cycle), label="AssignToLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, std_T_to_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    # plot.plot(arrival_rate_list, std_T_to_very_noisy_least_work_left_list, color=next(dark_color_cycle), label="AssignToVeryNoisyLeastWorkLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)
    plot.plot(arrival_rate_list, std_T_to_fewest_tasks_left_list, color=next(dark_color_cycle), label="AssignToFewestTasksLeft", marker=next(marker_cycle), linestyle="dotted", lw=2, mew=3, ms=5)

    plot.legend(fontsize=fontsize)
    plot.ylabel(r"$\sigma[T]$", fontsize=fontsize)
    plot.yscale("log")
    plot.xlabel(r"$\lambda$", fontsize=fontsize)

    # Save the plot
    plot.subplots_adjust(wspace=0.2)
    suptitle = plot.suptitle(
        r"$N_{\textrm{server}}= $" + f"{num_servers}, "
        r"$X \sim \textrm{Exp}(\lambda)$, "
        fr"$S \sim {task_service_time_rv.to_latex()}$, "
        r"$N_{\textrm{tasks}}= " + f"{num_tasks_to_recv}$, "
        r"$N_{\textrm{sim}}= " + f"{num_sim_runs}$"
    )
    plot.gcf().set_size_inches(15, 6)
    plot.savefig(f"plot_optimal_vs_ts_ET_vs_lambda_taskServiceTime_{type(task_service_time_rv).__name__}.png", bbox_extra_artists=(suptitle,), bbox_inches="tight")
    plot.gcf().clear()

    log(INFO, "Done")


def test_optimal_vs_ts(
    env: simpy.Environment,
    num_servers: int,
    task_service_time_rv: random_variable.RandomVariable,
):
    optimal_vs_ts(
        env=env,
        num_servers=num_servers,
        task_service_time_rv=task_service_time_rv,
        num_tasks_to_recv=1000,
        num_sim_runs=1,
    )


if __name__ == "__main__":
    optimal_vs_ts(
        env=simpy.Environment(),
        num_servers=10,
        # task_service_time_rv=random_variable.DiscreteUniform(min_value=1, max_value=1),
        task_service_time_rv=random_variable.Exponential(mu=1),
        num_tasks_to_recv=10000, # 10000,
        num_sim_runs=1,
    )
