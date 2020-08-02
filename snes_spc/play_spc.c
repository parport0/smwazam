/* Records SPC into wave file. Uses dsp_filter to give more authentic sound.

Usage: play_spc [test.spc]
*/

#include "spc.h"

#include "wave_writer.h"
#include "demo_util.h" /* error(), load_file() */

int main( int argc, char** argv )
{
	if (argc != 3) error( "usage: spc2wav in out" );;
	/* Create emulator and filter */
	SNES_SPC* snes_spc = spc_new();
	SPC_Filter* filter = spc_filter_new();
	if ( !snes_spc || !filter ) error( "Out of memory" );
	
	/* Load SPC */
	{
		/* Load file into memory */
		long spc_size;
		void* spc = load_file( argv[1], &spc_size );
		
		/* Load SPC data into emulator */
		error( spc_load_spc( snes_spc, spc, spc_size ) );
		free( spc ); /* emulator makes copy of data */
		
		/* Most SPC files have garbage data in the echo buffer, so clear that */
		spc_clear_echo( snes_spc );
		
		/* Clear filter before playing */
		spc_filter_clear( filter );
	}
	
	/* Record 120 seconds to wave file */
	wave_open( spc_sample_rate, argv[2] );
	wave_enable_stereo();
	while ( wave_sample_count() < 120 * spc_sample_rate * 2 )
	{
		/* Play into buffer */
		#define BUF_SIZE 2048
		short buf [BUF_SIZE];
		error( spc_play( snes_spc, BUF_SIZE, buf ) );
		
		/* Filter samples */
		spc_filter_run( filter, buf, BUF_SIZE );
		
		wave_write( buf, BUF_SIZE );
	}
	
	/* Cleanup */
	spc_filter_delete( filter );
	spc_delete( snes_spc );
	wave_close();
	
	return 0;
}
