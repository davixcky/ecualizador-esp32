import sys, pcbnew as k
b = k.LoadBoard(sys.argv[1]); b.BuildConnectivity()
k.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[1]); print('relleno ok')
