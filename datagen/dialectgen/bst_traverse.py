import re
import editdistance
from collections import defaultdict
from typing import List, Dict

import networkx as nx
import matplotlib.pyplot as plt

from datagen.dialectgen.graph_utils import build_graph_from_sql, TEMPLATE
from configs.config import USE_ANNOTATION

def convert_sql_to_dialect(sql_dict: Dict, table_dict: Dict, schema: Dict) -> str:
    # Create query graph
    ################################
    # val: number(float)/string(str)/sql(dict)
    # col_unit: (agg_id, col_id, isDistinct(bool))
    # val_unit: (unit_op, col_unit1, col_unit2)
    # table_unit: (table_type, col_unit/sql)
    # cond_unit: (not_op, op_id, val_unit, val1, val2)
    # condition: [cond_unit1, 'and'/'or', cond_unit2, ...]
    # sql {
    #   'select': (isDistinct(bool), [(agg_id, val_unit), (agg_id, val_unit), ...])
    #   'from': {'table_units': [table_unit1, table_unit2, ...], 'conds': condition}
    #   'where': condition
    #   'groupBy': [col_unit1, col_unit2, ...]
    #   'orderBy': ('asc'/'desc', [val_unit1, val_unit2, ...])
    #   'having': condition
    #   'limit': None/limit value
    #   'intersect': None/sql
    #   'except': None/sql
    #   'union': None/sql
    # }
    ################################
    
    dialect = ""
    # Build up query graph
    G = nx.MultiDiGraph()
    # To make every node name unique, we concanenate a tag after the node name with the current counting number 
    # node_posttag_dict: Dict[str, int] = defaultdict(int)
    # We consider a graph only represents a complete query, which indicates that for each of subquery, we make it as a graph respectively.
    if any(sql_dict[k] for k in ['intersect', 'except', 'union']):
        # For the main part of the query
        G, Rq = build_graph_from_sql(G, sql_dict, table_dict, schema)
        # nx.draw(G, arrows=True, with_labels=True, font_weight='bold')
        # # plt.show()
        dialect = generate_dialect_from_graph(G, Rq, table_dict, sql_dict=sql_dict)
        # G.add_node(G1)
        if sql_dict['intersect']:
            G1 = nx.MultiDiGraph(type ="subquery_node", primary = False)
            G1, Rq1 = build_graph_from_sql(G1, sql_dict['intersect'], table_dict, schema)
            dialect += generate_dialect_from_graph(G1, Rq1, table_dict, subq=True, conjStr='and')
            # G.add_node(G1)
            # G.add_edge(G1, G1, type='iue', label = 'and')
        if sql_dict['except']:
            G1 = nx.MultiDiGraph(type ="subquery_node", primary = False)
            G1, Rq1 = build_graph_from_sql(G1, sql_dict['except'], table_dict, schema)
            dialect += generate_dialect_from_graph(G1, Rq1, table_dict, subq=True, conjStr='except')
        if sql_dict['union']:
            G1 = nx.MultiDiGraph(type ="subquery_node", primary = False)
            G1, Rq1 = build_graph_from_sql(G1, sql_dict['union'], table_dict, schema)
            dialect += generate_dialect_from_graph(G1, Rq1, table_dict, subq=True, conjStr='or')
    else: 
        G, Rq = build_graph_from_sql(G, sql_dict, table_dict, schema)
        # nx.draw(G, arrows=True, with_labels=True, font_weight='bold')
        # plt.savefig("filename.png")
        # plt.show()
        dialect = generate_dialect_from_graph(G, Rq, table_dict)

    if dialect[-1] != '.': dialect += '.'

    # if any(sql_dict[k] for k in ['intersect', 'except', 'union']):
    #     # Get the main part of query to start
    #     G1 = [n for n in G.nodes if n.graph['primary']][0]
    #     # nx.draw(G1, arrows=True, with_labels=True, font_weight='bold')
    #     # plt.show()
        
    #     # Then traverse on each of the subquery
    #     for subquery_node in G.neighbors(G1):
    #         conjunction = G.edges[G1, subquery_node, 0]['label']
            
    # else:
    #     pStr, fStr, wStr, oStr, lStr = BST(G, Rq, lopen, lclose, pStr, fStr, wStr, oStr, lStr)
    #     desc = 'Find ' + pStr + ' for ' + fStr + '.' if 'each' in fStr else 'Find ' + pStr + '.'
    #     if wStr: 
    #         if oStr: desc += ' Return ' + lStr + ' results only for ' + wStr + ', ' + oStr + '.'
    #         else: desc += ' Return results only for ' + wStr + '.'
    #     elif oStr: desc += ' Return ' + lStr + ' results ' + oStr + '.'

    return ' '.join(dialect.split())

def BST(G, Rq, table_dict, lopen, lclose, pStr, wStr, gStr, oStr, lStr):
    def _make_lbl(clause, label, conj):
        if not clause: clause = label
        else:  clause += conj + label
        return clause
    def _make_lbl_w(clause, label, conj):
        # It will not have associated conjunction if it is the first predicate.
        if not conj: 
            clause = label + ' ' + clause
        else: 
            clause += ' ' + conj + ' ' + label
            
        return clause

    children = []
    lclose.append(Rq)

    # processing groupby
    for gamma_edge in G.edges:
        rel_node, attr_node, _ = gamma_edge
        # If group by primary key, the translation should be directly on query object;
        # Otherwise, it should be concatenate with column label.
        if rel_node == Rq and G.edges[rel_node, attr_node, 0]['type'] == 'gamma':
            if gStr: gStr += ' and '
            if G.nodes[attr_node]['primary']: gStr += G.nodes[Rq]['label']
            else: gStr += G.nodes[attr_node]['label'] + ' of ' + G.nodes[Rq]['label']

    # print(f"Rq:{Rq}")
    # processing predicates
    for attr_node in G.neighbors(Rq):
        # print(f"attr_node:{attr_node}")
        # LIMIT clause
        if G.edges[Rq, attr_node, 0]['type'] == 'limit':
            lStr = G.edges[Rq, attr_node, 0]['label'] + ' ' + G.nodes[attr_node]['label']
        # ORDERBY clause
        if G.edges[Rq, attr_node, 0]['type'] in ['ao', 'do', 'o']:
            oStr = G.edges[Rq, attr_node, 0]['label'] + ' '
            for r_edge in G.edges:
                func_node, attr_node1, _ = r_edge
                if attr_node1 == attr_node and G.edges[func_node, attr_node1, 0]['type'] == 'r': 
                    oStr += 'the ' + G.nodes[func_node]['label'] + ' '
            # if it is "start" node, do not need to concatenate table information.
            obj = G.nodes[attr_node]['label'] if '*' in attr_node else G.nodes[attr_node]['label'] + ' of ' + G.nodes[Rq]['label']
            oStr += obj
            
            # for value_node in G.neighbors(attr_node):
            #     # LIMIT clause
            #     if G.nodes[value_node]['type'] == 'value_node': 
            #         lStr = G.edges[attr_node, value_node, 0]['label'] + ' ' + G.nodes[value_node]['label']
        
        sPred = ""
        for value_node in G.neighbors(attr_node):
            if G.edges[attr_node, value_node, 0]['type'] == 'limit': 
                continue
            # Nested query in WHERE clause
            if isinstance(value_node, nx.MultiDiGraph):
                # print(f"Nested query found!")
                # For nested query, it would have some overlapping content with main query, we use fuzz match to make the decision.
                att_label = G.nodes[attr_node]['label1'] if 'label1' in G.nodes[attr_node] else G.nodes[Rq]['label'] + TEMPLATE["VAL_SEL"] + G.nodes[attr_node]['label']
                predicate = G.edges[attr_node, value_node, 0]['label'] 
                n_dialect = generate_dialect_from_graph(value_node, value_node.graph['Rq'], table_dict=table_dict, nested=True, att_label = att_label, predicate=predicate)
                sPred = att_label + ' ' + G.edges[attr_node, value_node, 0]['label'] + ' ' + n_dialect + ' '
            else:
                # print(f"value_node:{value_node}")
                if G.nodes[value_node]['type'] == 'value_node':
                    # HAVING clause
                    if G.edges[Rq, attr_node, 0]['type'] == 'h':
                        for r_edge in G.edges:
                            func_node, attr_node1, _ = r_edge
                            if attr_node1 == attr_node and G.edges[func_node, attr_node1, 0]['type'] == 'r':   
                                if not sPred:                             
                                    att_label = 'the ' + G.nodes[func_node]['label'] + ' '
                                    # if it is "start" node, do not need to concatenate table information.
                                    att_label += G.nodes[attr_node]['label'] if '*' in attr_node else G.nodes[attr_node]['label'] + ' of ' + G.nodes[Rq]['label']
                                    sPred = att_label + ' ' + G.edges[attr_node, value_node, 0]['label'] + ' ' + G.nodes[value_node]['label'] + ' '
                                    # sPred = G.nodes[Rq]['label'] + TEMPLATE["VAL_SEL"] + G.nodes[func_node]['label'] + ' '
                                else: 
                                    sPred += 'and ' + G.nodes[value_node]['label'] + ' '
                        # sPred += 'of ' + G.nodes[attr_node]['label'] + ' ' + G.edges[attr_node, value_node, 0]['label'] + ' ' + G.nodes[value_node]['label'] + ' '
                    # WHERE clause
                    elif G.edges[Rq, attr_node, 0]['type'] == 'theta':
                        if not sPred:
                            att_label = G.nodes[attr_node]['label1'] if 'label1' in G.nodes[attr_node] else G.nodes[Rq]['label'] + TEMPLATE["VAL_SEL"] + G.nodes[attr_node]['label']
                            sPred = att_label + ' ' + G.edges[attr_node, value_node, 0]['label'] + ' ' + G.nodes[value_node]['label'] + ' '
                        ## between and case
                        else: sPred += 'and ' + G.nodes[value_node]['label'] + ' '
                # JOIN clause
                if attr_node not in children and attr_node not in lclose and G.nodes[value_node]['type'] != 'value_node':
                    if G.edges[Rq, attr_node, 0]['type'] == 'theta': 
                        # sel_edges += 1
                        children.append(attr_node)
        if sPred: 
            wStr = _make_lbl_w(wStr, sPred, G.edges[Rq, attr_node, 0]['conj_name'])

    # processing join tables
    while children:
        rel_node = children.pop()

        # sel_edges -= 1
        # if sel_edges > 0: fStr +=  TEMPLATE["COORD_CONJ"]
        # elif sel_edges == 0: fStr += TEMPLATE["CONJ_NOUN"]
        # fStr += G.edges[Rq, rel_node, 0]['label'] + ' '
        lopen.append(rel_node)
    # processing projections
    for mu_edge in G.edges:
        attr_node, rel_node, _ = mu_edge
        if rel_node == Rq and G.edges[attr_node, rel_node, 0]['type'] == 'mu':
            sAgg = ""
            sDistinct = ""
            # Find if agg/distinct node exists
            for r_edge in G.edges:
                node, attr_node1, _ = r_edge
                if attr_node1 == attr_node and G.edges[node, attr_node1, 0]['type'] == 'r': 
                    sAgg = G.nodes[node]['label'] + ' '
                elif attr_node1 == attr_node and G.edges[node, attr_node1, 0]['type'] == 'distnt':
                    sDistinct = G.nodes[node]['label'] + ' '
            if '*' in attr_node: children.append((sAgg + sDistinct + G.nodes[attr_node]['label'], G.edges[attr_node, rel_node, 0]['label'], True))
            else: children.append((sAgg + sDistinct + G.nodes[attr_node]['label'], G.edges[attr_node, rel_node, 0]['label'], False))

    sPrj = ""
    while children:
        # if it is "star" node, do not need to concatenate table information.
        sNode, sEdge, is_star = children.pop()
        if is_star: sPrj += ' the ' + sNode + ' '
        else: sPrj += ' the ' + sNode + ' ' + sEdge + ' ' + G.nodes[Rq]['label']
        if len(children) > 0: sPrj += ','
    if sPrj: pStr = _make_lbl(pStr, sPrj, TEMPLATE["CONJ_PROJ"])

    if lopen:
        v = lopen.pop()
        pStr, wStr, gStr, oStr, lStr = BST(G, v, table_dict, lopen, lclose, pStr, wStr, gStr, oStr, lStr)

    return pStr, wStr, gStr, oStr, lStr


def generate_dialect_from_graph(G, Rq, table_dict, nested=False, att_label="", predicate="", subq=False, conjStr=None, sql_dict=None) -> str:
    use_annotation = USE_ANNOTATION
    pStr = fStr = wStr = gStr = oStr = lStr = ""
    dialect = ""
    lopen = []
    lclose = []
    pStr, wStr, gStr, oStr, lStr = BST(G, Rq, table_dict, lopen, lclose, pStr, wStr, gStr, oStr, lStr)
    join_conds = set()
    for theta_edge in G.edges:
        rel_node1, rel_node2, _ = theta_edge
        if any(G.nodes[n]['type'] != 'relation_node' for n in [rel_node1, rel_node2]): continue
        join_conds.add(G.edges[rel_node1, rel_node2, 0]['label'])
    # Only exisiting join we assign value to fStr.
    if join_conds:
        if use_annotation:
            join_conds = sorted(join_conds)
            join_key = '+'.join(join_conds)
            if (join_key not in table_dict['annotations']):
                print(f"NO ANNOATION FOR JOIN_KEY:{join_key}")
                return ""

            fStr = table_dict['annotations'][join_key]
        else:
            fStr = ""
            for join_cond in join_conds:
                parts = join_cond.split('=')
                fStr += parts[0].split('.')[0] + ' with ' + parts[1].split('.')[0] + ' '
    # Construct the dialect
    if not subq and not nested:
        dialect = 'Find ' + pStr
        group = False
        # If exists GROUPBY, and it is the same with fStr, we do not repeat twice.
        if gStr and fStr.strip() == gStr.strip():  
            group = True
            dialect += ' for each ' + gStr + '.' 
        elif fStr: dialect += ' regarding to ' + fStr + '.'
        else: dialect += '.'
        # If exists WHERE or HAVING 
        if wStr: 
            if sql_dict and sql_dict['intersect']: dialect += ' Return ' + lStr + ' results only for both '
            elif sql_dict and sql_dict['union']: dialect += ' Return ' + lStr + ' results only for combining '
            else: dialect += ' Return ' + lStr + ' results only for '
            dialect += wStr 
            if gStr and fStr.strip() != gStr.strip(): dialect += ' for each ' + gStr + ' '
            dialect += ' ' + oStr
        # If not exists WHERE or HAVING but exists one of GROUPBY/ORDERBY/LIMIT 
        elif (gStr and not group) or oStr:
            dialect += ' Return ' + lStr + ' results '
            if gStr and fStr.strip() != gStr.strip(): dialect += ' for each ' + gStr + ' '
            dialect += ' ' + oStr
    # If it is nested query.
    elif nested: 
        # print(f"att_label:{att_label}")
        # We classify nested query into two different types,
        # 1). Value Type (NOT IN, IN)
        # 2). Set Type (>, <, >=, <=, =, !=)
        if any(predicate == t for t in [TEMPLATE['in'], TEMPLATE['not in']]):
            #Extract the projection attribute
            prj_att = pStr.split(TEMPLATE['mu'])[0].split('the')[1].strip()
            # print(f"prj_att:{prj_att}, editdistance:{editdistance.eval(prj_att, att_label)}")
            # If the difference not greater than 3 or it is "id" column, 
            # we assume the object is the same between main and nested query.
            if editdistance.eval(prj_att, att_label) <= 3 or prj_att == 'id':
                pStr = 'the ones in ' + pStr.split(TEMPLATE['mu'])[1].strip()
            dialect = pStr
            if fStr: dialect += ' regarding to  ' + fStr + '.'
            if wStr: dialect += ' that ' + wStr
        else:
            dialect = pStr
            if fStr: dialect += ' regarding to  ' + fStr + '.'
            if wStr: dialect += ' that ' + wStr
            # If exists ORDERBY, it should follow "LIMIT 1" for value type;
            if oStr:
                if TEMPLATE['ao'] in oStr: dialect += ' with the least ' + oStr.split(TEMPLATE['ao'])[1] 
                elif TEMPLATE['do'] in oStr: dialect += ' with the most ' + oStr.split(TEMPLATE['do'])[1] 
    # If it is subquery, we only construct the latter part of dialect.
    else:
        if wStr:
            dialect = ' ' + conjStr + ' ' + wStr
            if gStr: dialect +=  ' for each ' + gStr
            dialect += ' ' + oStr
        # e.g. SELECT template_id FROM Templates EXCEPT SELECT template_id FROM Documents
        else:
            # It is single relation
            if not fStr: 
                for relation_node in G.nodes:
                    if G.nodes[relation_node]['type'] == 'relation_node': 
                        fStr =  G.nodes[relation_node]['label']
                        break
            dialect = ' ' + conjStr + ' the ones in ' + fStr

    return dialect
