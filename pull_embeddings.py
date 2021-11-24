import os
import time
import torch
import random
import argparse
import torch.distributed.rpc as rpc

arg_parser = argparse.ArgumentParser(description="rpc test arg parser")
arg_parser.add_argument("--world_size", type=int, default=2, help="world size like in mpi")
arg_parser.add_argument("--rank", type=int, help="rank of current node")
arg_parser.add_argument("--boss_addr", type=str, default="localhost", help="boss node address")
arg_parser.add_argument("--service_port", type=str, default="12345", help="port for communication")

args = arg_parser.parse_args()

os.environ["MASTER_ADDR"] = args.boss_addr
os.environ["MASTER_PORT"] = args.service_port
# os.environ["GLOO_SOCKET_IFNAME"] = "eth0"

M, K, N = 1024, 4096, 512

EMBEDDING_NUM = 1000000
EMBEDDING_DIM = 32

QPS = 23333
MIN_KEY_NUM = 233 # in each query
MAX_KEY_NUM = 666 # in each query

def embedding_lookup(query, table):
  return table.to_here()(query)

if __name__ == '__main__':
  if args.rank == 0:
    rpc.init_rpc("boss", rank=0, world_size=2)
    A, B = torch.rand((M, K)), torch.rand((K, N))

    C_local_generated = torch.matmul(A, B)
    C_local_generated = torch.matmul(A, B)
    C_local_generated = torch.matmul(A, B)

    local_func_call_start_time = time.time()
    C_local_generated = torch.matmul(A, B)
    local_func_call_end_time = time.time()

    C_rpc_generated = rpc.rpc_sync("worker1", torch.matmul, args=(A, B))
    C_rpc_generated = rpc.rpc_sync("worker1", torch.matmul, args=(A, B))
    C_rpc_generated = rpc.rpc_sync("worker1", torch.matmul, args=(A, B))

    rpc_call_start_time = time.time()
    C_rpc_generated = rpc.rpc_sync("worker1", torch.matmul, args=(A, B))
    rpc_call_end_time = time.time()

    print("local func call spent: ", local_func_call_end_time - local_func_call_start_time, " seconds")
    print("rpc call spent: ", rpc_call_end_time - rpc_call_start_time, " seconds")

    queries = [torch.randint(0, QPS, (1, random.randint(MIN_KEY_NUM, MAX_KEY_NUM)), 
					dtype=torch.int64).flatten() for _ in range(QPS)]

    emb_rref = rpc.remote("worker1", torch.nn.Embedding, args=(EMBEDDING_NUM, EMBEDDING_DIM))

    query_start_time = time.time()
    for query in queries:
      embeddings = rpc.rpc_sync("worker1", embedding_lookup, args=(query, emb_rref))
    query_end_time = time.time()
    print("C finish in 1 second, this script spent: ", query_end_time - query_start_time, " seconds")

  else:
    rpc.init_rpc("worker" + str(args.rank), rank=args.rank, world_size=2)
    
    # embedding_table = torch.nn.Embedding(EMBEDDING_NUM, EMBEDDING_DIM, padding_idx=0)


rpc.shutdown()
