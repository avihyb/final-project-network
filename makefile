.PHONY: all run clean
# PID_SERVER: PID of the server process. This is used to kill the server process after the client has completed the experiment.


# Define the range of iterations
NUMOFITERATIONS = 10
ITERATIONS = $(shell seq 1 $(NUMOFITERATIONS))

# Target to run the experiment
all: run

# Rule to start the server and client
run: create_files $(ITERATIONS)

create_files:
	@python3 createRandomFile.py $(NUMOFITERATIONS)

$(ITERATIONS):
	@echo "Running experiment with iteration $@"
	@{ \
		python3 QuicServer.py 7500 > Stats$@.txt & \
		PID_SERVER=$$!; \
		echo "Started server with PID $$PID_SERVER"; \
		sleep 1; \
		python3 QuicClient.py localhost 7500 $@; \
		wait $$PID_SERVER; \
		echo "Completed experiment with iteration $@"; \
	}

# Clean target to remove any generated files
clean:
	@echo "Cleaning up..."
	@rm -f *.pyc
	@rm -f Stats*.txt file_*.txt randomFile*.txt
	@sleep 0.5
	@echo "Cleaned up successfully."


# Kill the server and client processes
kill:
	@if pgrep -f QuicServer.py > /dev/null; then \
		echo "Killing QuicServer.py"; \
		while pgrep -f QuicServer.py > /dev/null; do \
			pkill -f QuicServer.py; \
			sleep 1; \
		done \
	else \
		echo "No QuicServer.py instances running"; \
	fi
	@if pgrep -f QuicClient.py > /dev/null; then \
		echo "Killing QuicClient.py"; \
		while pgrep -f QuicClient.py > /dev/null; do \
			pkill -f QuicClient.py; \
			sleep 1; \
		done \
	else \
		echo "No QuicClient.py instances running"; \
	fi
