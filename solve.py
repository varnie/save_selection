from typing import List


class Solution:
    def maxSubArray(self, nums: List[int]) -> int:

        prefix_sums = []
        for num in nums:
            prefix_sums.append(num if not prefix_sums else prefix_sums[-1] + num)

        max_sum = float('-inf')#max_sum = None
        cur_min = 0
        for p_sum in prefix_sums:
            max_sum = max(max_sum, p_sum - cur_min)
            cur_min = min(cur_min, p_sum)

        return max_sum


#assert Solution().maxSubArray([5,4,-1,7,8]) == 23
assert Solution().maxSubArray([-2,1]) == 1
