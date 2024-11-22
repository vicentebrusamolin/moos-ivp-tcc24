#!/bin/bash -e
#----------------------------------------------------------
#  Script: launch.sh
#  Author: Michael Benjamin
#  Mod by: Vicente Brusamolin
#  LastEd: Nov 7th 2024
#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
trap "kill -- -$$" EXIT SIGTERM SIGHUP SIGINT SIGKILL
TIME_WARP=1
COMMUNITY="alpha"
GUI="yes"

#----------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#----------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
	echo "launch.sh [SWITCHES] [time_warp]   "
	echo "  --help, -h           Show this help message            " 
	exit 0;
    elif [ "${ARGI}" = "--nogui" ] ; then
	GUI="no"
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then 
        TIME_WARP=$ARGI
    else 
        echo "launch.sh Bad arg:" $ARGI " Exiting with code: 1"
        exit 1
    fi
done


#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
echo "Launching All MOOS Communities with WARP:" $TIME_WARP
 source ~/anaconda3/etc/profile.d/conda.sh
 conda activate tccenv_conda
 
 # gnome-terminal -- ./TPNserver.py

 pAntler alfa.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
 pAntler mothership.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
 #pAntler port9000_alfagtw.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
 #pAntler port9001_alfa_gtw.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

 uMAC -t alfa.moos
