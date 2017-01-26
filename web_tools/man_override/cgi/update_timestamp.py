from sites import Sites

lifeStatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/lifestatus/manualLifeStatus.txt'
prodStatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/prodstatus/manualProdStatus.txt'
crabStatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/crabstatus/manualCrabStatus.txt'
io_bound_file = '/afs/cern.ch/user/c/cmssst/www/ioBound/io.txt'
real_cores_file = '/afs/cern.ch/user/c/cmssst/www/realCores/real.txt'
prod_cores_file = '/afs/cern.ch/user/c/cmssst/www/others/prod.txt'
cpu_bound_file = '/afs/cern.ch/user/c/cmssst/www/cpuBound/cpu.txt'

manual_overriden = Sites(lifeStatus_file, lifeStatus_file)
manual_overriden.write_changes(manual_overriden.sites)

prodstatus = Sites(prodStatus_file, prodStatus_file)
prodstatus.write_changes(prodstatus.sites)

crabstatus = Sites(crabStatus_file, crabStatus_file)
crabstatus.write_changes(crabstatus.sites)

io_bound = Sites(io_bound_file, io_bound_file)
io_bound.write_changes(io_bound.sites)

real_cores = Sites(real_cores_file, real_cores_file)
real_cores.write_changes(real_cores.sites)

prod_cores = Sites(prod_cores_file, prod_cores_file)
prod_cores.write_changes(prod_cores.sites)

cpu_bound = Sites(cpu_bound_file, cpu_bound_file)
cpu_bound.write_changes(cpu_bound.sites)
