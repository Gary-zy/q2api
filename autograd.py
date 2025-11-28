"""
微型自动微分引擎 (Micrograd)
仅使用 Python 基础特性实现，无任何深度学习框架依赖
"""

class Value:
    """
    存储标量值并追踪计算图的节点
    """

    def __init__(self, data, _children=(), _op='', label=''):
        self.data = data                    # 标量值
        self.grad = 0.0                     # 梯度，初始为0
        self._backward = lambda: None       # 反向传播函数
        self._prev = set(_children)         # 父节点（计算图中的前驱）
        self._op = _op                      # 产生此节点的操作
        self.label = label                  # 可选标签，用于调试

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad})"

    # ==================== 运算符重载 ====================

    def __add__(self, other):
        """加法: self + other"""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')

        def _backward():
            # d(a+b)/da = 1, d(a+b)/db = 1
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad
        out._backward = _backward

        return out

    def __radd__(self, other):  # other + self
        return self + other

    def __mul__(self, other):
        """乘法: self * other"""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')

        def _backward():
            # d(a*b)/da = b, d(a*b)/db = a
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward

        return out

    def __rmul__(self, other):  # other * self
        return self * other

    def __neg__(self):  # -self
        return self * -1

    def __sub__(self, other):  # self - other
        return self + (-other)

    def __rsub__(self, other):  # other - self
        return other + (-self)

    def __pow__(self, n):
        """幂运算: self ** n (n 为常数)"""
        assert isinstance(n, (int, float)), "仅支持常数幂"
        out = Value(self.data ** n, (self,), f'**{n}')

        def _backward():
            # d(x^n)/dx = n * x^(n-1)
            self.grad += n * (self.data ** (n - 1)) * out.grad
        out._backward = _backward

        return out

    def __truediv__(self, other):  # self / other
        return self * (other ** -1)

    def __rtruediv__(self, other):  # other / self
        return other * (self ** -1)

    # ==================== 反向传播 ====================

    def backward(self):
        """
        从当前节点反向传播梯度到所有叶子节点
        使用拓扑排序确保正确的计算顺序
        """
        # 拓扑排序
        topo = []
        visited = set()

        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)

        # 从输出节点开始，梯度为1
        self.grad = 1.0

        # 按逆拓扑顺序反向传播
        for node in reversed(topo):
            node._backward()


# ==================== 测试用例 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("微型自动微分引擎测试")
    print("=" * 50)

    # 测试: f(x, y) = x² * y + y + 2
    # 在 x=3, y=4 处求导

    print("\n测试函数: f(x, y) = x² * y + y + 2")
    print("求值点: x = 3, y = 4")
    print()

    # 创建输入变量
    x = Value(3.0, label='x')
    y = Value(4.0, label='y')

    # 构建计算图: f = x² * y + y + 2
    x_squared = x ** 2           # x² = 9
    term1 = x_squared * y        # x² * y = 36
    term2 = term1 + y            # x² * y + y = 40
    f = term2 + 2                # x² * y + y + 2 = 42

    print(f"前向计算: f(3, 4) = {f.data}")
    print()

    # 反向传播
    f.backward()

    print("反向传播结果:")
    print(f"  ∂f/∂x = {x.grad}")
    print(f"  ∂f/∂y = {y.grad}")
    print()

    # 手动验证
    print("手动验证:")
    print("  f(x, y) = x² * y + y + 2")
    print("  ∂f/∂x = 2xy = 2 * 3 * 4 = 24  ✓" if x.grad == 24 else "  ∂f/∂x 错误!")
    print("  ∂f/∂y = x² + 1 = 9 + 1 = 10   ✓" if y.grad == 10 else "  ∂f/∂y 错误!")
    print()

    # 更复杂的测试
    print("=" * 50)
    print("额外测试: g(a, b) = (a + b) * (a - b)")
    print("求值点: a = 5, b = 3")
    print()

    a = Value(5.0, label='a')
    b = Value(3.0, label='b')

    g = (a + b) * (a - b)  # = a² - b² = 25 - 9 = 16

    print(f"前向计算: g(5, 3) = {g.data}")

    g.backward()

    print(f"  ∂g/∂a = {a.grad}  (应为 2a = 10)")
    print(f"  ∂g/∂b = {b.grad}  (应为 -2b = -6)")
    print()

    print("=" * 50)
    print("所有测试完成!")
