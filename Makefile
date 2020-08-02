CXXFLAGS = -O3
CXX = g++
SRC = demo_util.c wave_writer.c play_spc.c dsp.cpp SNES_SPC.cpp \
	  SNES_SPC_misc.cpp SNES_SPC_state.cpp spc.cpp SPC_DSP.cpp SPC_Filter.cpp
SNES_SPC = snes_spc

all: spc2wav
spc2wav:
	$(CXX) $(CXXFLAGS) $(addprefix $(SNES_SPC)/,$(SRC)) -o $@

clean:
	rm -f spc2wav

.PHONY: clean
