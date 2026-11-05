def classFactory(iface):
    from .plugin import QGISAIPlugin
    return QGISAIPlugin(iface)
