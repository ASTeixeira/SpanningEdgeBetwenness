import networkx as nx
import scipy as sp
import scipy.sparse
import numpy as np
import scipy.linalg.lapack as la
from scipy.linalg import lu
from operator import itemgetter
from disjoint_set import DisjointSet
import time


def calc_edges_SEB(temp_matrix, edges, prev, nEdge, calcdet, calcNMSTsDet, mapaux, mapsets):
    seb = {}
    
    for edge in np.arange(prev, nEdge):
        u, v = edges[edge][0], edges[edge][1]
        s = mapsets[u]
        d = mapsets[v]
        
        if s == d:
            value = {(u, v) : 0}
            seb.update(value)
            continue
        
        vgraph = []
        for el in calcdet[mapaux[u]]:
            if el != s and el != d:
                vgraph.append(el)
                
        matrix = temp_matrix[vgraph, :] [:, vgraph]
        #calculated as in the Java version using Lapack factorization
        LU, piv, info = la.dgetrf(matrix)
        detCalc = 0
        for x in np.diag(LU):
            detCalc += np.log10(np.abs(x))
        eMSTs = detCalc
        #eMSTs = np.linalg.det(matrix)
        value = {(u, v) : round(eMSTs-calcNMSTsDet[mapaux[u]],3)}
        seb.update(value)
        
    return seb


def seb_weighted(G): 
    size = len(G.nodes())  
    edges = []
    for e in G.edges():
        edges.append([e[0],e[1],G[e[0]][e[1]]['weight']])
    edges = sorted(edges, key = itemgetter(2))
    nEdges = len(edges)
    current_weight = edges[0][2]

    ds = DisjointSet()
    mapsets = np.arange(size)
    mapaux = np.full(size, -1)
    vaux = []
    seb_values = {}
    temp_matrix = np.zeros((size, size))

    nmsts = 0

    f = open("SEBstats","w+")

    prev = 0
    nEdge = 0

    while(True):


        if(nEdge < nEdges and edges[nEdge][2] == current_weight): 
            
            u, v = edges[nEdge][0], edges[nEdge][1]
            if u not in vaux:
                vaux.append(u)
            if v not in vaux:
                vaux.append(v)

            s = mapsets[u]
            d = mapsets[v]

            print("edge: " + str(u) + " " + str(v) + " ")

            temp_matrix[s][d] += -1
            temp_matrix[d][s] += -1
            temp_matrix[s][s] += 1
            temp_matrix[d][d] += 1

            if(not ds.connected(u,v)):
                ds.union(u,v)
                
            nEdge += 1
            
        elif prev != nEdge:
            mapid = 0
            for i in range(size):
                setid = ds.find(i)
                if mapaux[setid] == -1:
                    mapaux[setid] = mapid
                    mapaux[i] = mapid
                    mapid += 1
                else:
                    mapaux[i] = mapaux[setid]

            print("mapaux: ", mapaux)

            calcdet = []
            for i in range(mapid):
                calcdet.append([])

            for i in range(len(vaux)):
                if mapsets[vaux[i]] not in calcdet[mapaux[vaux[i]]]:
                    calcdet[mapaux[vaux[i]]].append(mapsets[vaux[i]])

            #print(mapid)
            calcNMSTsDet = np.zeros(mapid)
            #print(calcNMSTsDet)
            for i in range(len(calcdet)):
                if len(calcdet[i]) != 0:
                    vgraph = calcdet[i].copy()
                    vgraph.pop(0)
                    matrix = temp_matrix[vgraph, :] [:, vgraph]
                    print(matrix, flush=True)
                    time.sleep(2)
                    LU, piv, info = la.dgetrf(matrix)
                    detCalc = 0
                    for x in np.diag(LU):
                        detCalc += np.log10(np.abs(x))
                    msts = detCalc
                    #msts = np.linalg.det(matrix)
                    nmsts += msts
                    calcNMSTsDet[i] = msts

            seb = calc_edges_SEB(temp_matrix, edges, prev, nEdge, calcdet, calcNMSTsDet, mapaux, mapsets)
            seb_values.update(seb)

            prev = nEdge
            print("nEdge: ", nEdge, " nEdges: ", nEdges)
            if (nEdge >= nEdges):
                break

            current_weight += 1
            temp_matrix = np.zeros((mapid, mapid))
            vaux = []
            mapsets = mapaux.copy()
            mapaux = np.full(size, -1)

        else:
            current_weight += 1

    nx.set_edge_attributes(G, seb_values,'SEB')
    #print("Total of Minimum Spanning Trees: " + str(round(nmsts)) + "\n")
    f.write("Total of Minimum Spanning Trees: 10^" + str(round(nmsts)) + "\n")
    for e in G.edges():
        #print(e)
        f.write("" + str(e[0]) + " " + str(e[1]) + " " + str(G[e[0]][e[1]]['SEB']) + "\n")
    f.close()



def seb_unweighted(G): 
    f = open("SEBstats","w+")

    #Kirchhoff's Theorem
    Laplacian = sp.sparse.csr_matrix.toarray(nx.laplacian_matrix(G))
    toMSTs = np.delete(Laplacian, 0, 0)
    toMSTs = np.delete(toMSTs, 0, 1)


    LU, piv, info = la.dgetrf(toMSTs)
    detCalc = 0
    for x in np.diag(LU):
        detCalc += np.log10(np.abs(x))
    nMSTs = detCalc

    f.write("Total of Minimum Spanning Trees: 10^" + str(round(nMSTs,3)) + "\n")

    x = 0
    for e in G.edges():
        print(x)
        x += 1
        eMSTs = calc_SEB(Laplacian, e, nMSTs)
        G[e[0]][e[1]]['SEB'] = eMSTs
        f.write("" + str(e[0]) + " " + str(e[1]) + " 10^" + str(eMSTs) + "\n")
    f.write("################################")
    f.close()

def calc_SEB(matrix, e, nMSTs):
    toMSTs = np.delete(matrix, (int(e[0]),int(e[1])), 0)
    toMSTs = np.delete(toMSTs, (int(e[0]),int(e[1])), 1)


    #calculated as in the Java version using Lapack factorization
    LU, piv, info = la.dgetrf(toMSTs)
    detCalc = 0
    for x in np.diag(LU):
        detCalc += np.log10(np.abs(x))
    eMSTs = detCalc
    

    return round(eMSTs-nMSTs,3)

G = nx.read_weighted_edgelist("simplenet", nodetype=int)
seb_weighted(G)

"""
output_file = open("SEBtimesScipy","w+")

output_file.write("scipy factorization" + "\n")
G = nx.read_edgelist("powerout", nodetype=int)
s = time.process_time()
seb_unweighted(G)
e = time.process_time()
d = e - s
output_file.write("power network: " + str(d) + "\n")

G1 = nx.read_edgelist("bio-celegans_out", nodetype=int)
s = time.process_time()
seb_unweighted(G1)
e = time.process_time()
d = e - s
output_file.write("bio network: " + str(d) + "\n")

G2 = nx.read_edgelist("ca-netscience_out", nodetype=int)
s = time.process_time()
seb_unweighted(G2)
e = time.process_time()
d = e - s
output_file.write("netscience network: " + str(d) + "\n")

G3 = nx.read_edgelist("soc-dolphins_out", nodetype=int)
s = time.process_time()
seb_unweighted(G3)
e = time.process_time()
d = e - s
output_file.write("dolphins network: " + str(d) + "\n")

G4 = nx.read_edgelist("fb_out", nodetype=int)
s = time.process_time()
seb_unweighted(G4)
e = time.process_time()
d = e - s
output_file.write("fb network: " + str(d) + "\n")

G5 = nx.read_edgelist("web-edu_out", nodetype=int)
s = time.process_time()
seb_unweighted(G5)
e = time.process_time()
d = e - s
output_file.write("edu network: " + str(d) + "\n")

print("FINISHED")
"""