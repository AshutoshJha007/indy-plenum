from plenum.test.helper import stopNodes, waitForViewChange, \
    sendReqsToNodesAndVerifySuffReplies
from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data
from plenum.test.pool_transactions.helper import \
    disconnect_node_and_ensure_disconnected, \
    reconnect_node_and_ensure_connected
from plenum.test.test_node import ensureElectionsDone, ensure_node_disconnected
from plenum.test.view_change.helper import ensure_view_change
from plenum.test.view_change.helper import start_stopped_node


# Do not remove these imports
from plenum.test.pool_transactions.conftest import client1, wallet1, client1Connected, looper


def test_selection_f_plus_one_quorum(
        looper,
        txnPoolNodeSet,
        allPluginsPath,
        tdir,
        tconf,
        client1,
        wallet1,
        client1Connected):
    """
    Check that quorum f + 1 is used for primary selection
    when initiated by CurrentState messages.

    Assumes that view change quorum is n - f.
    Assumes that primaries selection in round robin fashion.
    """

    # Ensure that we have 4 nodes in total
    all_nodes = list(txnPoolNodeSet)
    assert 4 == len(all_nodes)
    alpha, beta, delta, gamma = all_nodes
    initial_view_no = alpha.viewNo

    # Make one node lagging by switching it off for some time
    lagging_node = gamma
    non_lagging_nodes = [alpha, beta, delta]
    disconnect_node_and_ensure_disconnected(looper,
                                            all_nodes,
                                            lagging_node,
                                            stopNode=True)
    looper.removeProdable(lagging_node)

    # Make nodes to perform view change
    ensure_view_change(looper, non_lagging_nodes)
    ensureElectionsDone(looper=looper, nodes=non_lagging_nodes, numInstances=2)
    ensure_all_nodes_have_same_data(looper, nodes=non_lagging_nodes)

    # Stop two more of active nodes
    # (but not primary, which is Beta (because of round robin selection))
    stopped_nodes = [alpha]  # TODO: add one more here
    for stopped_node in stopped_nodes:
        disconnect_node_and_ensure_disconnected(looper, txnPoolNodeSet,
                                                stopped_node, stopNode=True)
        looper.removeProdable(stopped_node)

    # Start lagging node back
    restarted_node = start_stopped_node(
        lagging_node, looper, tconf, tdir, allPluginsPath)
    active_nodes = [beta, delta, restarted_node]

    # Check that primary selected
    expected_view_no = initial_view_no + 1
    ensureElectionsDone(looper=looper, nodes=active_nodes,
                        numInstances=2, customTimeout=30)
    waitForViewChange(looper, active_nodes, expectedViewNo=expected_view_no)

    sendReqsToNodesAndVerifySuffReplies(looper, wallet1, client1, numReqs=1)
