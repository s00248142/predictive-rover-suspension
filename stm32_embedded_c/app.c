/*******************************************************************************
* File Name: app.c
* Description: 6_step 3-phase PWM motor operation using ST MCSDK API
*   The app_loop() function is called from the main while() loop in main.c
*   main.c initialise the hardware mostly from ST Cube MX configurator.
*   Key additions to main.c include CAN bus messaging and control of
*   'target_speed' in this file and app_loop().
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
*******************************************************************************/

#include "app.h"
#include "mc_api.h"   // ST MCSDK gives access to MC_StartMotor1, etc...

#define MAX_SPEED 600 // In RPM
#define MIN_SPEED 5
#define DURATION 100 // Ramp rate. Lower is faster but unstable in 6--step

static int motor_enabled = 0;
int16_t target_speed = 0;
int16_t bemf_speed = 0;
int16_t abs_speed = 0;  // Temporary variable for soft-stop
int16_t direction_sensed = 1; // 1 is forward, -1 is reverse
int16_t cmd = 0;
int16_t last_cmd = 0;
static uint32_t last_speed_update_ms = 0; // Rate Limit
static uint32_t last_softstop_update_ms = 0;

/* Restart variables. */
int16_t restart_cmd = 0;
int restart_after_stop = 0;
static uint32_t restart_ts = 0;
static int restart_delay = 0;
int waiting_for_start = 1;
int waiting_for_stop = 0;

/* MCSDK-specific variables */
static uint32_t fault_ts = 0; // Fault time-stamp
static int fault_active = 0;
MCI_State_t motor_status; // IDLE, RUN, FAULT etc...

/* Function Prototypes */
int soft_stop_init(int16_t bemf_speed);
int direction_change(int16_t bemf_speed);

/******************************************************************************* 
* Primary Application Loop 
*   Called from main.c continuously and update motor speed control through
*   ST MCSDK API functions.
*******************************************************************************/

void app_loop(void)
{
	bemf_speed = MC_GetMecSpeedAverageMotor1(); // back EMF speed from API
    cmd = target_speed; // 'target_speed' is the primary link between
    motor_status = MC_GetSTMStateMotor1(); //

	/* Restart delay required if changing direction. */
    if (restart_delay)
    {
        if ((HAL_GetTick() - restart_ts) < 500)
        {
            return; // wait 500 ms
        }

        restart_delay = 0;
        waiting_for_start = 1;
    }

    /* Don't try to start motor unless a target speed is set. */
    if (!motor_enabled && cmd == 0)
    {
        return;   // don't start unless commanded
    }

    /* Ensure motor is up after power-on or fault. */
    if (waiting_for_start)
    {
        if (motor_status == IDLE)
        {
            // Clamp before sending cmd
            if (cmd > MAX_SPEED) cmd = MAX_SPEED;
            if (cmd < -MAX_SPEED) cmd = -MAX_SPEED;
            MC_ProgramSpeedRampMotor1(cmd, DURATION); // Set signed target first
            MC_StartMotor1(); // Enable motor.
            motor_enabled = 1;
            last_cmd = cmd;

            return;
        }
       	else if (motor_status == RUN){
            fault_active = 0;
            waiting_for_start = 0;
            restart_after_stop = 0;
        }
        return;
    }

    /* Check and acknowledge faults */
	if (motor_status == FAULT_NOW || motor_status == FAULT_OVER){

		if (!fault_active)
			{
				fault_active = 1; // Private fault flag
				fault_ts = HAL_GetTick();   // ms timestamp
			}

		// Wait 3 seconds before clearing fault.
		if ((HAL_GetTick() - fault_ts) > 3000)
		{
			MC_AcknowledgeFaultMotor1(); // Clear fault
			fault_active = 0;
			motor_enabled = 0;
			waiting_for_start = 1;
		}

		return; // Loop until fault cleared
	}


    /* Soft-Stop Catcher. Deflect if target keeps same direction and big. */
	if (waiting_for_stop
			&& cmd != 0
			&& ((cmd * last_cmd) > 0) // Same direction
			&& ( ((cmd + last_cmd / 2) < -25)
					|| ((cmd + last_cmd / 2) > 25) ) ) // Big
	{
		waiting_for_stop = 0;
		return;
	}

	else if (waiting_for_stop && abs_speed > 25){
		if ((HAL_GetTick() - last_softstop_update_ms) >= 35)
		{
			// Slow down first
		    MC_ProgramSpeedRampMotor1((1 * direction_sensed), DURATION);
		    last_softstop_update_ms = HAL_GetTick();
		}

	    soft_stop_init(bemf_speed); // Update abs_speed using same function.
		return;
	}

	if (waiting_for_stop && abs_speed < 25) {

		MC_StopMotor1();    // Then stop motor when speed is below 25 RPM

		waiting_for_stop = 0;
		waiting_for_start = 1; // Force attempt to start on next loop cycle
		motor_enabled = 0;
		abs_speed = 0; // Reset abs_speed for next soft-stop cycle.
		last_cmd = 0; // Resets to allow 6-step to change sign.
		if (restart_after_stop)
		{
		    target_speed = restart_cmd; // Keep opposite direction command alive
		}
		restart_ts = HAL_GetTick();
		restart_delay = 1;

		return; // Allow for fresh entry from top of loop for sending speed
	}


    // Initiate soft-stop if direction changes or near-zero target
    if (motor_enabled && (	((cmd > 0 && last_cmd < 0)
    						|| (cmd < 0 && last_cmd > 0)
							|| ((cmd < 10) && (cmd > -10)))	) ) {
    	restart_cmd = cmd; // Store command while stopping and restarting motor
    	restart_after_stop = 1;
    	waiting_for_stop = soft_stop_init(bemf_speed);
    	return;
    }


    // Clamp before sending cmd
    if (cmd > MAX_SPEED) cmd = MAX_SPEED;
    if (cmd < -MAX_SPEED) cmd = -MAX_SPEED;

    // Send motor speed with rate limit
    if ((HAL_GetTick() - last_speed_update_ms) >= 5)  // ~200 Hz
    {
        MC_ProgramSpeedRampMotor1(cmd, DURATION);
        last_speed_update_ms = HAL_GetTick();
    }

    last_cmd = cmd;
}

/* Soft stop init function feeds the Soft-Stop Catcher, with to create smooth
 * transitions for halting or changing direction. */
int soft_stop_init(int16_t bemf_speed){

    if (bemf_speed < 0){
    	direction_sensed = -1;
    	abs_speed = -bemf_speed;
    }
    else {
    	direction_sensed = 1;
    	abs_speed = bemf_speed;
    }

    return 1; // Set waiting-for-stop flag
}

/******************************* End of file **********************************/

