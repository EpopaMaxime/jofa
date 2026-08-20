import pymysql

# Use PyMySQL as a drop-in replacement for mysqlclient (MySQLdb).
# Spoof version so Django accepts the driver (PyMySQL reports 1.x).
pymysql.version_info = (2, 2, 1, 'final', 0)
pymysql.install_as_MySQLdb()
