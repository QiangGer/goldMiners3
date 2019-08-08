# coding=utf-8
import stock as s
import stocks as ss

# def main():

#     res = s.main(Fastperiod=2,Slowperiod=3,Signalperiod=5)
#     print(res)

# main()

import random
import math
import copy
import matplotlib.pyplot as plt

from scipy.optimize import fsolve


class GA(object):
    def __init__(self, generation, population_size, pc, pm, bound_list, delta, opt):
        self.generation = generation
        self.population_size = population_size
        self.pc = pc
        self.pm = pm
        self.bound_list = bound_list
        self.delta = delta
        self.opt = opt
        self.max = 0  ## 当前代数使函数值达到最大的个体
        self.min = 0  ## 当前代数使函数值达到最小的个体
        self.elitist = 0  # 精英策略,保留迄今为止最好的个体
        self.encodeLength = self.getEncodedLength(self.delta, self.bound_list)  # 每一个变量需要的染色体位数
        self.choromosome_length = sum(self.encodeLength)  # 染色体总位数

    # 初始化种群
    # 返回一个 种群大小 × 染色体长度 的二维数组
    def speciesOrigin(self):
        population = []
        for i in range(self.population_size):
            temporary = []  # 染色体暂存器
            for j in range(self.choromosome_length):
                temporary.append(random.randint(0, 1))  # 随机产生一个染色体,由二进制数组成
            population.append(temporary)  # 将染色体添加到种群中
        return population  # 将种群返回,种群是个二维数组

    # 选择种群中个体适应度较大的个体
    # 运用轮盘赌的方式选择,适应度越大,留下的概率越大
    # 新种群的个体全部取自旧种群,而后再进行交叉及变异处理
    def selection(self, population, fitness_value):
        new_fitness = []
        total_fitness = self.sum(fitness_value)  # 将所有的适应度求和

        for i in range(len(fitness_value)):
            new_fitness.append(fitness_value[i] / total_fitness)  # 将所有个体的适应度正则化,所有个体求和后的值为1

        self.cumsum(new_fitness)

        ms = []  # 该数组用于产生随机数,作为轮盘赌的选择依据
        pop_len = len(population)

        for i in range(pop_len):  # 产生种群个数的随机值
            ms.append(random.random())
        ms.sort()  # 存活的种群排序

        fitIndex = 0
        newIndex = 0  # 这两个index用于遍历数组
        new_pop = copy.deepcopy(population)  # 这是新一代种群,暂时copy旧种群

        # 轮盘赌方式
        while newIndex < pop_len:  # 使得新种群全部取自旧种群
            if ms[newIndex] < new_fitness[fitIndex]:
                new_pop[newIndex] = population[fitIndex]
                newIndex += 1
            else:
                fitIndex += 1
        return new_pop

    # 交叉操作
    def crossover(self, population):
        for i in range(len(population) - 1):
            if random.random() < self.pc:  # pc是概率阈值
                cpoint = random.randint(0, len(population[0]))
                # 在种群个数内随机生成单点交叉点
                temporary1 = []
                temporary2 = []

                temporary1.extend(population[i][0:cpoint])
                temporary1.extend(population[i + 1][cpoint:len(population[i])])
                # 将tmporary1作为暂存器，暂时存放第i个染色体中的前0到cpoint个基因，
                # 然后再把第i+1个染色体中的后cpoint到第i个染色体中的基因个数，补充到temporary2后面

                temporary2.extend(population[i + 1][0:cpoint])
                temporary2.extend(population[i][cpoint:len(population[i])])
                # 将tmporary2作为暂存器，暂时存放第i+1个染色体中的前0到cpoint个基因，
                # 然后再把第i个染色体中的后cpoint到第i个染色体中的基因个数，补充到temporary2后面
                population[i] = temporary1
                population[i + 1] = temporary2
        # 第i个染色体和第i+1个染色体基因重组/交叉完成
        return population

    # 变异操作
    def mutation(self, population):
        px = len(population)
        # 求出种群中所有种群/个体的个数
        py = len(population[0])
        # 染色体/个体基因的个数
        for i in range(px):
            if random.random() < self.pm:  # pm是概率阈值
                mpoint = random.randint(0, py - 1)
                #
                if population[i][mpoint] == 1:
                    # 将mpoint个基因进行单点随机变异，变为0或者1
                    population[i][mpoint] = 0
                else:
                    population[i][mpoint] = 1
        return population

    # 解码,从二进制转化为十进制,返回种群中所有个体编码完成后的十进制数
    # 就是循环迭代了decode方法
    def translation(self, population):
        temporary = []
        for i in range(len(population)):
            total = self.decode(population[i])
            temporary.append(total)
        return temporary

    # 计算适应度和
    def sum(self, fitness_value):
        total = 0
        for i in range(len(fitness_value)):
            total += fitness_value[i]
        return total

    # 计算适应度斐波纳挈列表
    # 传入的fitness已经做了正则化处理,这里是为了求出累积的适应度,用于轮盘赌的选择
    def cumsum(self, fitness):
        for i in range(len(fitness) - 2, -1, -1):  # range(start,stop,[step])
            total = 0
            j = 0
            while j <= i:
                total += fitness[j]
                j += 1
            fitness[i] = total
            fitness[len(fitness) - 1] = 1

    # 更新精英, 选取适应度更大的个体
    def updateElitist(self, best_individual):
        elitist = []
        best = []
        elitist.append(F(self.decode(self.elitist)))
        best.append(F(self.decode(best_individual)))
        if self.fitness(best) > self.fitness(elitist):
            self.elitist = best_individual

    # 寻找当前这一代最好的适应度和个体,保留在result结果集中
    def bestFitnessOfThisGeneration(self, population, fitness_value):
        bestindividual = population[0]
        bestfitness = fitness_value[0]

        for i in range(1, len(population)):  # 循环找出最大的适应度，适应度最大的也就是最好的个体
            if fitness_value[i] > bestfitness:
                bestfitness = fitness_value[i]
                bestindividual = population[i]

        return [bestindividual, bestfitness]

    # 寻找这一代函数值的最值,适应度的标定可能需要用到
    def bestFunctionValueOfThisGeneration(self, function_value):
        temp = copy.deepcopy(function_value)  # 为了不改变原数组顺序,深层复制原数组
        temp.sort()
        self.max = temp[len(temp) - 1]
        self.min = temp[0]

    # 变量的数量不确定,该函数用于确定每一个变量所需要的编码长度
    # 染色体长度选择公式:
    # 2^(x-1) <= (up_bound-lower_bound) * 10^(delta) < 2^(x)
    # 其中,delta为小数点后的位数,x为染色体长度
    # 需要传入变量的精度,不考虑不同变量精度不一致的情况;还需要变量的上下界,作为数组传入
    def getEncodedLength(self, delta, bound_list, x0=30):
        lengths = []
        for i in bound_list:
            lower = i[0]
            upper = i[1]
            # lamnda 代表匿名函数f(x)=0,x0代表搜索的初始解
            res = fsolve(lambda x: (2 ** (x - 1) - (upper - lower) * (10 ** delta)), x0)
            length = int(res[0])
            lengths.append(length)
        return lengths

    # x∈[lower_bound, upper_bound]
    # x = lower_bound + decimal(chromosome)×(upper_bound - lower_bound) / (2 ^ chromosome_size - 1)
    # lower_bound: 函数定义域的下限
    # upper_bound: 函数定义域的上限
    # chromosome_size: 染色体的长度
    # 通过上述公式,我们就可以成功地将二进制染色体串解码成[lower_bound, upper_bound]区间中的十进制实数解
    def decode(self, individual):
        variables = len(self.encodeLength)  # 获取变量的数目
        decodedvalues = []  # 用于存储解码得到的值
        start = 0
        for i in range(variables):
            length = self.encodeLength[i]
            total = 0
            for j in range(start, length + start):
                total = total + individual[j] * math.pow(2, j - start)
            lower_bound = self.bound_list[i][0]
            upper_bound = self.bound_list[i][1]
            total = lower_bound + total * (upper_bound - lower_bound) / (
                    math.pow(2, length) - 1)
            decodedvalues.append(total)
            start += length
        return decodedvalues

    # 计算种群在某一目标函数下的值
    # 将种群population翻译成变量数组后传给目标函数即可
    def function(self, population):
        result = []
        temporary = self.translation(population)  # 将2进制转化为10进制,来计算函数值
        for i in range(len(temporary)):
            x = temporary[i]
            result.append(F(x))
        return result

    def plot(self, results):
        X = []
        Y = []

        for i in range(self.generation):
            X.append(i)
            Y.append(results[i][0])

        plt.plot(X, Y)
        plt.show()

    def main(self):
        results = []

        # 生成初始种群
        population = self.speciesOrigin()
        self.elitist = population[self.population_size - 1]
        # 精英策略,再添加一格用于保留最佳个体
        population.append(population[self.population_size - 1])

        for i in range(self.generation):
            # 计算种群在目标函数的值
            function_value = self.function(population)
            # 更新目前为止的最优(最大和最小)目标函数值,用于适应度标定
            self.bestFunctionValueOfThisGeneration(function_value)
            # 算出这一代的适应度
            fitness_value = self.fitness(function_value)

            # 寻找最好的适应度和个体,最好的适应度就是最大的适应度（无论是求目标函数的最大值还是最小值）
            best_individual, best_fitness = self.bestFitnessOfThisGeneration(population, fitness_value)
            self.updateElitist(best_individual)
            # 将精英的值和函数值保存,用于绘图,应该可以保证图像曲线不会抖动,（但偶尔图像会出现抖动,没有精力去查了）
            results.append([F(self.decode(self.elitist)), self.decode(self.elitist)])
            # 打印的结果则输出当代最好个体的值
            print("当前代数", i + 1, "函数值", F(self.decode(best_individual)), "变量取值", self.decode(best_individual))

            population = self.selection(population, fitness_value)
            population = self.crossover(population)
            population = self.mutation(population)
            # 交叉变异结束后,直接将精英放置在种群最后一位
            population[self.population_size] = self.elitist

        self.plot(results)
        results.sort()
        if self.opt == "min":
            print("函数的最小值为：", results[0][0], "变量取值为：", results[0][1])
        else:
            print("函数的最大值为：", results[len(results) - 1][0], "变量取值为：", results[len(results) - 1][1])

    # --------------------------------------------------
    # 以上内容基本上不用修改
    # 以下须根据需求设计适应度函数和目标函数以及算法变量
    # --------------------------------------------------

    # 定义函数值对应的适应度
    # 目前设置的是 动态（划掉）线性标定
    # 对于动态线性标定：
    #   最小值时： f(k) = Fmax - Fk + ksi * r^(k-1)
    #   最大值是： f(k) = Fmin + Fk + ksi * r^(k-1)
    #       k是代数,max和min是本代函数值的最值,r是一个常数,r∈[0.9,0.999],
    #       ksi是一个常数,还不知道选择标准,网上一文献给了2,暂时用2,但实验后发现,该值的取值应和目标函数的值域有关
    # 理想的适应度函数应该使所有函数值都能等概率的映射到大于零的值,同时各个适应度之间相对差别大
    # [1000,1001,1002,1003]之间的相对差别就比不上[1,2,3,4]
    # 适应度变化有两个目的：
    #   1维持个体之间的合理差距,加速竞争
    #   2避免个体之间的差距过大,限制竞争
    # 约束条件也在此体现,具体做法是在适应度函数中加入惩罚机制,不满足约束条件的个体的适应度相应降低或置零
    # 适应度的标定方法严重影响算法效果,务必按实际需求好好设计
    # 适应度的标定方法严重影响算法效果,务必按实际需求好好设计
    # 适应度的标定方法严重影响算法效果,务必按实际需求好好设计
    def fitness(self, function_value):
        # ksi = 2
        # r = 0.9
        fitness_value = []
        fitness_value = copy.deepcopy(function_value)
        # if self.opt == "min":
        #     for i in range(len(function_value)):
        #         temporary = self.max - function_value[i] + ksi  # * (r ** i)
        #         fitness_value.append(temporary)  # 将适应度添加到列表中
        # else:
        #     for i in range(len(function_value)):
        #         temporary = self.min + function_value[i] + ksi  # * (r ** i)
        #         fitness_value.append(temporary)  # 将适应度添加到列表中

        return fitness_value


# 目标函数
# x为变量数组,哪怕只有一个变量,也需用x[0]表示
def F(x):
    # res = x[1] * math.sin(2 * math.pi * x[0]) + x[0] * math.cos(2 * math.pi * x[1])
    # res = x[0] + x[1]
    res = ss.main(Fastperiod=x[0], Slowperiod=x[1], Signalperiod=x[2])
    return res


if __name__ == '__main__':
    generation = 6  # 迭代次数
    population_size = 30  # 种群大小
    bound_list = [[5, 15], [20, 40], [5, 25]]  # 变量上下界
    delta = 0  # 变量精度（小数点后;整数写0）
    pc = 0.7  # 配对概率
    pm = 0.01  # 变异概率
    opt = "max"  # 目标函数要最大值还是最小值
    ga = GA(generation, population_size, pc, pm, bound_list, delta, opt)
    ga.main()
