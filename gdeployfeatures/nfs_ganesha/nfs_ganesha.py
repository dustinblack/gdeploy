"""
Add functions corresponding to each of the actions in the json file.
The function should be named as follows <feature name>_<action_name>
"""
from gdeploylib import defaults, Helpers, Global

helpers = Helpers()

def nfs_ganesha_create_cluster(section_dict):
    global helpers
    cluster_nodes = get_cluster_nodes(section_dict)
    if Global.trace:
        Global.logger.info("Retrieved cluster nodes.")
    section_dict['ha_name'] = section_dict.pop('ha-name')
    if not len(cluster_nodes) == len(section_dict.get('vip')):
            print "\nError: Provide virtual IPs for all the hosts in "\
                    "the cluster-nodes"
            helpers.cleanup_and_quit()
    vips, section_dict['vip_list'] = get_host_vips(section_dict, cluster_nodes)
    section_dict['value'] = "on"
    ymls = [ defaults.GANESHA_BOOTSTRAP, defaults.GANESHA_PUBKEY,
            defaults.COPY_SSH, defaults.SHARED_MOUNT,
            defaults.SET_AUTH_PASS, defaults.PCS_AUTH,
             defaults.GANESHA_CONF_CREATE, defaults.DEFINE_SERVICE_PORTS,
             defaults.ENABLE_GANESHA, defaults.GANESHA_VOL_EXPORT]
    section_dict = get_base_dir(section_dict)
    if Global.trace:
        for ymll in ymls:
            Global.logger.info("Executing %s."%ymll)
    return section_dict, ymls

def nfs_ganesha_destroy_cluster(section_dict):
    global helpers
    section_dict = get_base_dir(section_dict)
    helpers.write_to_inventory('cluster_nodes',
            section_dict.get('cluster-nodes'))
    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_DISABLE)
    return section_dict, defaults.GANESHA_DISABLE

def nfs_ganesha_add_node(section_dict):
    new_nodes = section_dict.get('nodes')
    vips, vip_list = get_host_vips(section_dict, new_nodes)
    data = []
    for node, vip in zip(new_nodes, vips):
        nodes_list = {}
        nodes_list['host'] = node
        nodes_list['vip'] = vip
        data.append(nodes_list)
    section_dict['nodes_list'] = data
    section_dict = get_base_dir(section_dict)
    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_BOOTSTRAP)
        Global.logger.info("Executing %s."%defaults.GANESHA_ADD_NODE)
    return section_dict, [defaults.GANESHA_BOOTSTRAP,
                                defaults.GANESHA_ADD_NODE]

def nfs_ganesha_delete_node(section_dict):
    section_dict = get_base_dir(section_dict)
    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_DELETE_NODE)
    return section_dict, defaults.GANESHA_DELETE_NODE

def nfs_ganesha_export_volume(section_dict):
    section_dict['value'] = "on"
    section_dict = get_base_dir(section_dict)
    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_VOL_CONFS)
        Global.logger.info("Executing %s."%defaults.GANESHA_VOL_EXPORT)
    return section_dict, [defaults.GANESHA_VOL_CONFS,
            defaults.GANESHA_VOL_EXPORT ]

def nfs_ganesha_unexport_volume(section_dict):
    section_dict['value'] = "off"
    section_dict = get_base_dir(section_dict)
    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_VOL_EXPORT)
    return section_dict, defaults.GANESHA_VOL_EXPORT

def nfs_ganesha_refresh_config(section_dict):
    del_lines = list_to_string(section_dict.get('del-config-lines'))
    # Split the string which is `|' delimited. Escaped `|' is handled gracefully
    if del_lines:
        section_dict['del-config-lines'] = helpers.split_string(del_lines, '|')

    add_lines = list_to_string(section_dict.get('add-config-lines'))
    if add_lines:
        section_dict['add-config-lines'] = helpers.split_string(add_lines, '|')

    block_name = section_dict.get('block-name')
    section_dict['block-name'] = block_name

    config_block = list_to_string(section_dict.get('config-block'))
    if config_block:
        section_dict['config-block'] = helpers.split_string(config_block, '|')

    section_dict['ha-conf-dir'] = section_dict.get('ha-conf-dir')
    section_dict = get_base_dir(section_dict)

    if config_block:
        section_dict['config-block'].insert(0, '%s {'%block_name)
        section_dict['config-block'].append('}\n')

    if Global.trace:
        Global.logger.info("Executing %s."%defaults.GANESHA_REFRESH_CONFIG)
    return section_dict, defaults.GANESHA_REFRESH_CONFIG

def get_cluster_nodes(section_dict):
    global helpers
    cluster_nodes = section_dict.get('cluster-nodes')
    if Global.hosts:
        if not set(cluster_nodes).issubset(set(Global.hosts)):
            print "\nError: cluster-nodes are not subset of the 'hosts' "\
                    "provided"
            helpers.cleanup_and_quit()
    else:
        Global.hosts = cluster_nodes
    helpers.write_to_inventory('cluster_nodes', cluster_nodes)
    helpers.write_to_inventory('master_node', [cluster_nodes[0]])
    section_dict['cluster_hosts'] = ','.join(node for node in cluster_nodes)
    section_dict['master_node'] = cluster_nodes[0]
    return cluster_nodes

def get_host_vips(section_dict, cluster):
    VIPs = section_dict.get('vip')
    if len(cluster) != len(VIPs):
        print "\nError: The number of cluster_nodes provided and VIP "\
                "given doesn't match. Exiting!"
        helpers.cleanup_and_quit()
    vip_list = []
    for host, vip in zip(cluster, VIPs):
        key = 'VIP_' + host
        vip_list.append("%s=\"%s\"" %(key, vip))
    vip_list = '\n'.join(vip_list)
    return VIPs, vip_list

def get_base_dir(section_dict):
    section_dict['base_dir'] = Global.base_dir
    section_dict['ha_base_dir'] = '/var/run/gluster/shared_storage/nfs-ganesha'
    return section_dict

def list_to_string(l):
    # If l is a list of lines, join and return string
    if type(l) is list:
        return ",".join(l)
    else:
        # Return the string
        return l
