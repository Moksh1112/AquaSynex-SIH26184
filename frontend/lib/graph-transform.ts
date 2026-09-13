export interface GraphNode {
  id: string;
  label: string;
  metadata: any;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  metadata: any;
}

export interface GraphResponse {
  case_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TrailStep {
  id: string;
  type: 'TRANSFER' | 'WITHDRAWAL' | 'ATM';
  fromNode?: GraphNode;
  toNode?: GraphNode;
  amount?: number;
  timestamp?: string;
  description: string;
}

export interface FlowEntity {
  id: string;
  label: string;
  name: string;
  value: string;
  type: 'SOURCE' | 'PASS-THROUGH' | 'WITHDRAWAL' | 'ATM' | 'UNRESOLVED';
  tone: string;
}

export function getNodeDisplayName(node?: GraphNode): string {
  if (!node) return 'Unknown';
  if (node.label === 'Account') {
    return node.metadata.bank_name || node.metadata.account_number || node.id;
  } else if (node.label === 'Transaction') {
    return node.metadata.transaction_id ? `Transaction #${node.metadata.transaction_id}` : 'Transaction';
  } else if (node.label === 'Withdrawal') {
    return node.metadata.withdrawal_id ? `Withdrawal #${node.metadata.withdrawal_id}` : 'Cash Withdrawal';
  } else if (node.label === 'ATM') {
    const address = node.metadata.address ? ` (${node.metadata.address})` : '';
    return node.metadata.atm_id ? `${node.metadata.atm_id}${address}` : 'ATM Location';
  }
  return node.id;
}

export function transformGraph(data: GraphResponse | null) {
  if (!data || !data.nodes || !data.edges) {
    return { steps: [], flow: [] };
  }

  const nodesMap = new Map<string, GraphNode>();
  data.nodes.forEach(n => nodesMap.set(n.id, n));

  const steps: TrailStep[] = [];
  const flow: FlowEntity[] = [];
  const addedToFlow = new Set<string>();

  const addFlowEntity = (nodeId: string, role: FlowEntity['type']) => {
    if (addedToFlow.has(nodeId)) return;
    const n = nodesMap.get(nodeId);
    if (!n) return;

    let name = n.id;
    let value = '';

    if (n.label === 'Account') {
      name = n.metadata.bank_name || 'Unknown Bank';
      value = n.metadata.account_number || n.id;
    } else if (n.label === 'Transaction') {
      name = n.metadata.transaction_id ? `Transaction #${n.metadata.transaction_id}` : 'Transaction';
      value = n.metadata.amount ? `₹${n.metadata.amount.toLocaleString()}` : '';
    } else if (n.label === 'Withdrawal') {
      name = n.metadata.withdrawal_id ? `Withdrawal #${n.metadata.withdrawal_id}` : 'Cash Withdrawal';
      value = n.metadata.amount ? `₹${n.metadata.amount.toLocaleString()}` : '';
    } else if (n.label === 'ATM') {
      name = n.metadata.atm_id || 'ATM Location';
      value = n.metadata.address || '';
    }

    let tone = 'slate';
    if (role === 'SOURCE') tone = 'cyan';
    if (role === 'PASS-THROUGH') tone = 'blue';
    if (role === 'WITHDRAWAL') tone = 'amber';
    if (role === 'ATM') tone = 'red';

    flow.push({
      id: n.id,
      label: n.label,
      name,
      value,
      type: role,
      tone
    });
    addedToFlow.add(nodeId);
  };

  // We trace the path based on explicit semantic edges
  // 1. Find TRANSFERRED_TO edges
  const transfers = data.edges.filter(e => e.type === 'TRANSFERRED_TO');
  
  // Sort transfers by timestamp if available
  transfers.sort((a, b) => {
    const tA = a.metadata?.timestamp || '';
    const tB = b.metadata?.timestamp || '';
    return tA.localeCompare(tB);
  });

  transfers.forEach((edge, index) => {
    const fromNode = nodesMap.get(edge.source);
    const toNode = nodesMap.get(edge.target);
    
    if (fromNode && toNode) {
      steps.push({
        id: `edge-${index}`,
        type: 'TRANSFER',
        fromNode,
        toNode,
        amount: edge.metadata?.amount,
        timestamp: edge.metadata?.timestamp,
        description: 'Transfer'
      });

      addFlowEntity(fromNode.id, index === 0 ? 'SOURCE' : 'PASS-THROUGH');
      addFlowEntity(toNode.id, 'PASS-THROUGH');
    }
  });

  // 2. Find MADE_WITHDRAWAL edges
  const withdrawals = data.edges.filter(e => e.type === 'MADE_WITHDRAWAL');
  withdrawals.forEach((wEdge, index) => {
    const accountNode = nodesMap.get(wEdge.source);
    const withdrawalNode = nodesMap.get(wEdge.target);
    
    if (accountNode && withdrawalNode) {
      steps.push({
        id: `withdraw-${index}`,
        type: 'WITHDRAWAL',
        fromNode: accountNode,
        toNode: withdrawalNode,
        amount: withdrawalNode.metadata?.amount, // Might be empty due to backend collision
        timestamp: withdrawalNode.metadata?.timestamp,
        description: 'Withdrawal'
      });
      addFlowEntity(accountNode.id, 'PASS-THROUGH');
      addFlowEntity(withdrawalNode.id, 'WITHDRAWAL');

      // Check if there is an AT_ATM edge from this withdrawal
      const atmEdge = data.edges.find(e => e.type === 'AT_ATM' && e.source === withdrawalNode.id);
      if (atmEdge) {
        const atmNode = nodesMap.get(atmEdge.target);
        if (atmNode) {
          steps.push({
            id: `atm-${index}`,
            type: 'ATM',
            fromNode: withdrawalNode,
            toNode: atmNode,
            description: 'ATM Location'
          });
          addFlowEntity(atmNode.id, 'ATM');
        }
      }
    }
  });

  // Adjust flow endpoint tags
  if (flow.length > 0) {
    const last = flow[flow.length - 1];
    if (last.type === 'PASS-THROUGH') {
      last.type = 'UNRESOLVED';
      last.tone = 'red';
    }
  }

  return { steps, flow };
}
