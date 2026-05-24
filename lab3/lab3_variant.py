import lab3_io as io
import lab3_compute as compute
import lab3_plotter as plotter


def main():
    params = io.read_params()
    results = compute.run_simulation(params)
    io.print_results(results)
    plotter.plot_all(results, params)


if __name__ == "__main__":
    main()
