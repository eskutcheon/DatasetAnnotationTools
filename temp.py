import numpy as np
import matplotlib.pyplot as plt


# import os
# import torchvision.io as IO


# source_dir = r"C:\Users\Jacob\Documents\MSU Thesis Work\dirtydashcams\New folder"
# file_paths = [os.path.join(source_dir, p) for p in os.listdir(source_dir)]

# for path in file_paths:
#     img = IO.read_image(path, IO.ImageReadMode.RGB)
#     img = img[:, :, :(img.shape[2]-120)]
#     IO.write_png(img, path, compression_level=3)

eps = 1e-4
num_epochs = 50
#schedule_func = lambda t, a, b, T: a*np.tanh(t/T) + b
# sigmoid function
#schedule_func = lambda t, a, b, c, d: a/(1 + d*np.exp(-b*(t-c))) + eps
exponent = lambda t, T: 0.01*T*t - 0.001*(T**2)
schedule_func = lambda t, a, T: a/(1 + T*np.exp(-exponent(t, T))) + eps
#sched_growth = lambda t, a, b, T: a*(b/T)*(1/np.cosh(b*t/T))**2
epoch_range = np.linspace(0, num_epochs, 1000)
epochs = np.arange(0, num_epochs, 1)
a = 0.5
# b = 0.5
# c = 5
# d = 50
# probability = schedule_func(epoch_range, a, b, c, d)
probability = schedule_func(epoch_range, a, num_epochs)
#prob_growth = sched_growth(epoch_range, 0.5, 1, 30)
exact_probs = schedule_func(epochs, a, num_epochs)

plt.figure(facecolor="lightgrey")
plt.plot(epoch_range, probability, linewidth=6)
#plt.plot(epoch_range, prob_growth)
plt.scatter(epochs, exact_probs, s=50, color='red', edgecolors='black', zorder=2)
plt.axis('auto')
plt.tick_params(axis='both', labelsize=18)
plt.grid()
plt.xlabel('epochs\n', fontsize=24)
plt.ylabel('probability\n', fontsize=24)
plt.title('Probability Schedule using $T=50$', fontsize=32)
#plt.set_facecolor('lightgrey')
plt.show()